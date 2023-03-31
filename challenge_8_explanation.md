# Challenge 8 — adding an inventory item through the API

**The task:** add an item to Inventory through the API, where the metadata
carries `year`, `actors`, `imdb_rating`, `rotten_tomatoes_rating` and
`film_locations`.

This is written as if to a developer who has the endpoint in front of them and
cannot get it to accept anything.

---

## 1. Start by reproducing it, not by reading the code

Before changing a line, get the failure in your terminal. With the server
running and the demo data loaded:

```bash
curl -s -X POST http://127.0.0.1:8000/inventory/ \
  -H 'Content-Type: application/json' \
  -d '{"name":"Inception","type":1,"language":37,"tags":[6],
       "metadata":{"year":2010,"actors":["Leonardo DiCaprio"],
                   "imdb_rating":8.8,"rotten_tomatoes_rating":87}}'
```

On the original code that returns:

```json
{"type":{"non_field_errors":["Invalid data. Expected a dictionary, but got int."]},
 "language":{"non_field_errors":["Invalid data. Expected a dictionary, but got int."]},
 "tags":[{"non_field_errors":["Invalid data. Expected a dictionary, but got int."]}],
 "metadata":["Value must be valid JSON."]}
```

Four errors from one request. Read them carefully — they are **two separate
bugs**, and fixing only one leaves you still at HTTP 400, which is the point
at which most people conclude the payload must be wrong and start guessing.
It is not the payload.

## 2. Bug one: the serializer can read, but it cannot write

Here is the original serializer:

```python
class InventorySerializer(serializers.ModelSerializer):
    type = InventoryTypeSerializer()
    language = InventoryLanguageSerializer()
    tags = InventoryTagSerializer(many=True)
```

Declaring `type = InventoryTypeSerializer()` says "this field is a nested
object". That is exactly what you want when **rendering** — the client gets
`"type": {"id": 1, "name": "Movie"}` rather than a bare `1`. But the same
declaration is what DRF validates **incoming** data against, so on a POST it
now demands `"type": {"id": 1, "name": "Movie"}` too. That is where
`Expected a dictionary, but got int` comes from.

The instinct is to send the dictionary. Don't — it fails differently.
`ModelSerializer` refuses to write a nested relation at all; you would get
`The .create() method does not support writable nested fields by default`.
The nested declaration cannot be made to work on input.

**The fix is to stop asking one class to do both jobs.** Reads and writes want
opposite representations, so give them a class each:

```python
class InventorySerializer(serializers.ModelSerializer):
    """Read: relations expanded inline."""
    type = InventoryTypeSerializer(read_only=True)
    language = InventoryLanguageSerializer(read_only=True)
    tags = InventoryTagSerializer(many=True, read_only=True)


class InventoryWriteSerializer(serializers.ModelSerializer):
    """Write: relations as primary keys."""
    type = serializers.PrimaryKeyRelatedField(queryset=InventoryType.objects.all())
    language = serializers.PrimaryKeyRelatedField(queryset=InventoryLanguage.objects.all())
    tags = serializers.PrimaryKeyRelatedField(
        queryset=InventoryTag.objects.all(), many=True, required=False
    )
    metadata = serializers.DictField()
```

`PrimaryKeyRelatedField` takes the integer you were sending all along, and
because it is given a `queryset` it also checks the row exists — so a bad
`type` id becomes a clean 400 instead of an `IntegrityError` at insert time.

The view then picks per method:

```python
def get_serializer_class(self):
    return InventoryWriteSerializer if self.request.method == "POST" else InventorySerializer
```

and answers with the read representation so the client still gets the nested
object back:

```python
def create(self, request, *args, **kwargs):
    serializer = self.get_serializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    inventory = services.create_inventory(**serializer.validated_data)
    return Response(InventorySerializer(inventory).data, status=201)
```

## 3. Bug two: `metadata` was never JSON

The fourth error, `"metadata": ["Value must be valid JSON."]`, is unrelated to
the first three. The original view did this:

```python
metadata = InventoryMetaData(**request.data['metadata'])
request.data['metadata'] = metadata.dict()
```

`InventoryMetaData` declares `imdb_rating: Decimal`, so pydantic helpfully
coerces `8.8` into `Decimal('8.8')`, and `.dict()` hands that `Decimal`
straight back. `json.dumps` cannot serialise a `Decimal` — it raises
`TypeError` — and DRF catches that and reports it as "Value must be valid
JSON". The validation you added is what broke the write.

Round-trip through pydantic's own JSON encoder instead, which knows to render
a `Decimal` as a number:

```python
return json.loads(model.json())   # {"imdb_rating": 8.8, ...} — plain floats
```

This is the general lesson worth taking away: **validating a value and
serialising it are different operations.** A validator is entitled to give you
back a richer type than you put in, and if the next step is a database column
that only speaks JSON, you have to convert deliberately.

## 4. Where the validation should live

The original code validated metadata inside the view, and mutated
`request.data` in place to do it. Both are worth avoiding:

- mutating `request.data` works for a JSON body but raises on a form-encoded
  one, because that arrives as an immutable `QueryDict`;
- a rule that lives in a view is a rule no management command, admin action
  or Celery task can reuse, so the next writer of inventory data quietly skips
  it.

Move it into the service layer, which the view calls:

```python
@transaction.atomic
def create_inventory(*, name, type, language, metadata, tags=()):
    validated_metadata = metadata_registry.validate(type.name, metadata)
    inventory = Inventory.objects.create(
        name=name, type=type, language=language, metadata=validated_metadata
    )
    if tags:
        inventory.tags.set(tags)
    return inventory
```

`@transaction.atomic` matters because the tags are attached *after* the
insert. Without it, a failure between the two leaves a tagless row behind.

## 5. Adding `film_locations`

Add it to the schema with a default, so the rows already in the database —
which predate the field — keep validating:

```python
class InventoryMetaData(BaseModel):
    year: int
    actors: list[str]
    imdb_rating: Decimal
    rotten_tomatoes_rating: int
    film_locations: list[str] = []

    class Config:
        extra = "forbid"
```

`extra = "forbid"` is the part that earns its keep. This repository's own seed
data contained `rotten_toamtoes_rating` — a transposition in "tomatoes" that
sat in the fixture unnoticed. Without `forbid`, pydantic drops the unknown key
silently and stores a row missing its rating; with it you get:

```json
{"metadata":[{"loc":["rotten_tomatoes_rating"],"msg":"field required","type":"value_error.missing"},
             {"loc":["rotten_toamtoes_rating"],"msg":"extra fields not permitted","type":"value_error.extra"}]}
```

A `JSONField` will accept any shape you give it, so the schema is the only
thing standing between you and a column full of near-misses.

If a future inventory type needs a different shape, register one rather than
widening the shared schema:

```python
class EpisodeMetadata(InventoryMetaData):
    season: int
    episode: int

metadata_registry.register("Episode", EpisodeMetadata)
```

Anything not registered keeps using the default.

## 6. The working request

```bash
curl -s -X POST http://127.0.0.1:8000/inventory/ \
  -H 'Content-Type: application/json' \
  -d '{"name":"Inception","type":1,"language":37,"tags":[6],
       "metadata":{"year":2010,
                   "actors":["Leonardo DiCaprio","Joseph Gordon-Levitt"],
                   "imdb_rating":8.8,
                   "rotten_tomatoes_rating":87,
                   "film_locations":["Paris, France","Tokyo, Japan"]}}'
```

```json
{"id":18,"name":"Inception","type":{"id":1,"name":"Movie"},
 "language":{"id":37,"name":"English"},
 "tags":[{"id":6,"name":"Sci-Fi","is_active":true}],
 "metadata":{"year":2010,"actors":["Leonardo DiCaprio","Joseph Gordon-Levitt"],
             "imdb_rating":8.8,"rotten_tomatoes_rating":87,
             "film_locations":["Paris, France","Tokyo, Japan"]},
 "created_at":"2026-09-24T21:38:55.404345Z"}
```

HTTP 201. That transcript is real output, captured in
[`docs/api-transcript.txt`](docs/api-transcript.txt).

## 7. Finally, write the test

The bug was invisible because nothing exercised the endpoint. Add the test
that would have caught it:

```python
def test_post_creates_an_item(api_client, language, inventory_type, inventory_tag, metadata):
    response = api_client.post(
        reverse("inventory:inventory-list"),
        {"name": "Inception", "type": inventory_type.id, "language": language.id,
         "tags": [inventory_tag.id], "metadata": metadata},
        format="json",
    )

    assert response.status_code == 201, response.data
    assert response.json()["type"] == {"id": inventory_type.id, "name": "Movie"}
    assert response.json()["metadata"]["imdb_rating"] == 8.8
```

Two assertions beyond the status code, and both matter: the first pins the
read/write split (the response must still nest), the second pins the `Decimal`
fix (`8.8`, not `"8.8"`). See `tests/inventory/test_views.py` and
`tests/inventory/test_schemas.py`.
