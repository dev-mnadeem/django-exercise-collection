"""The inventory HTTP surface.

`test_post_creates_an_item` is the important one: before the read/write
serializer split and the metadata JSON fix, every POST to this endpoint
returned 400 and the API could not create inventory at all.
"""

from datetime import datetime, timezone

import pytest
from django.urls import reverse

from interview.inventory.models import Inventory, InventoryLanguage, InventoryTag, InventoryType

pytestmark = pytest.mark.django_db


def test_post_creates_an_item(api_client, language, inventory_type, inventory_tag, metadata):
    response = api_client.post(
        reverse("inventory:inventory-list"),
        {
            "name": "Inception",
            "type": inventory_type.id,
            "language": language.id,
            "tags": [inventory_tag.id],
            "metadata": metadata,
        },
        format="json",
    )

    assert response.status_code == 201, response.data
    body = response.json()
    assert body["name"] == "Inception"
    # The response echoes the nested read representation.
    assert body["type"] == {"id": inventory_type.id, "name": "Movie"}
    assert body["language"]["name"] == "English"
    assert [tag["name"] for tag in body["tags"]] == ["Action"]
    assert body["metadata"]["imdb_rating"] == 8.7
    assert Inventory.objects.count() == 1


def test_post_rejects_invalid_metadata(api_client, language, inventory_type):
    response = api_client.post(
        reverse("inventory:inventory-list"),
        {
            "name": "Broken",
            "type": inventory_type.id,
            "language": language.id,
            "metadata": {"year": 2010},
        },
        format="json",
    )

    assert response.status_code == 400
    assert "metadata" in response.json()
    assert Inventory.objects.count() == 0


def test_post_rejects_an_unknown_foreign_key(api_client, language, metadata):
    response = api_client.post(
        reverse("inventory:inventory-list"),
        {"name": "X", "type": 9999, "language": language.id, "metadata": metadata},
        format="json",
    )

    assert response.status_code == 400
    assert "type" in response.json()


def test_list_is_paginated_three_at_a_time(api_client, make_inventory):
    for index in range(5):
        make_inventory(name=f"Title {index}")

    response = api_client.get(reverse("inventory:inventory-list"))

    assert response.status_code == 200
    body = response.json()
    assert body["count"] == 5
    assert len(body["results"]) == 3
    assert body["next"] is not None


def test_list_honours_offset_and_limit(api_client, make_inventory):
    for index in range(5):
        make_inventory(name=f"Title {index}")

    response = api_client.get(reverse("inventory:inventory-list"), {"limit": 2, "offset": 4})

    body = response.json()
    assert body["count"] == 5
    assert len(body["results"]) == 1
    assert body["next"] is None


def test_list_limit_is_capped(api_client, make_inventory):
    make_inventory()

    response = api_client.get(reverse("inventory:inventory-list"), {"limit": 10_000})

    assert response.status_code == 200
    assert len(response.json()["results"]) == 1


def test_list_filters_by_created_after(api_client, make_inventory):
    old = make_inventory(name="Old")
    new = make_inventory(name="New")
    Inventory.objects.filter(pk=old.pk).update(created_at=datetime(2023, 1, 1, tzinfo=timezone.utc))
    Inventory.objects.filter(pk=new.pk).update(created_at=datetime(2024, 1, 1, tzinfo=timezone.utc))

    response = api_client.get(reverse("inventory:inventory-list"), {"created_after": "2023-06-01"})

    assert response.status_code == 200
    assert [row["name"] for row in response.json()["results"]] == ["New"]


def test_created_after_endpoint(api_client, make_inventory):
    old = make_inventory(name="Old")
    make_inventory(name="New")
    Inventory.objects.filter(pk=old.pk).update(created_at=datetime(2023, 1, 1, tzinfo=timezone.utc))

    response = api_client.get(
        reverse("inventory:inventory-created-after"), {"created_after": "2023-06-01"}
    )

    assert response.status_code == 200
    assert [row["name"] for row in response.json()["results"]] == ["New"]


def test_created_after_rejects_a_malformed_date(api_client):
    response = api_client.get(
        reverse("inventory:inventory-created-after"), {"created_after": "last tuesday"}
    )

    assert response.status_code == 400
    assert "created_after" in response.json()


def test_retrieve(api_client, inventory):
    response = api_client.get(reverse("inventory:inventory-detail", kwargs={"id": inventory.id}))

    assert response.status_code == 200
    assert response.json()["name"] == inventory.name


def test_retrieve_missing_id_is_404_not_500(api_client):
    """This used to raise Inventory.DoesNotExist straight out of the view."""
    response = api_client.get(reverse("inventory:inventory-detail", kwargs={"id": 999999}))

    assert response.status_code == 404


def test_patch_updates_a_field(api_client, inventory, language, inventory_type, metadata):
    response = api_client.patch(
        reverse("inventory:inventory-detail", kwargs={"id": inventory.id}),
        {"name": "Renamed"},
        format="json",
    )

    assert response.status_code == 200, response.data
    assert response.json()["name"] == "Renamed"


def test_patch_rejects_invalid_metadata(api_client, inventory):
    response = api_client.patch(
        reverse("inventory:inventory-detail", kwargs={"id": inventory.id}),
        {"metadata": {"year": "nope"}},
        format="json",
    )

    assert response.status_code == 400


def test_delete(api_client, inventory):
    response = api_client.delete(reverse("inventory:inventory-detail", kwargs={"id": inventory.id}))

    assert response.status_code == 204
    assert Inventory.objects.count() == 0


def test_put_is_not_offered(api_client, inventory):
    response = api_client.put(
        reverse("inventory:inventory-detail", kwargs={"id": inventory.id}),
        {"name": "X"},
        format="json",
    )

    assert response.status_code == 405


@pytest.mark.parametrize(
    "list_url,detail_url,model,payload",
    [
        (
            "inventory:inventory-tags-list",
            "inventory:inventory-tags-detail",
            InventoryTag,
            {"name": "Noir"},
        ),
        (
            "inventory:inventory-languages-list",
            "inventory:inventory-languages-detail",
            InventoryLanguage,
            {"name": "Welsh"},
        ),
        (
            "inventory:inventory-types-list",
            "inventory:inventory-types-detail",
            InventoryType,
            {"name": "Trailer"},
        ),
    ],
)
def test_reference_data_crud(api_client, list_url, detail_url, model, payload):
    created = api_client.post(reverse(list_url), payload, format="json")
    assert created.status_code == 201, created.data
    pk = created.json()["id"]

    listed = api_client.get(reverse(list_url))
    assert listed.status_code == 200
    assert listed.json()["count"] == 1

    fetched = api_client.get(reverse(detail_url, kwargs={"id": pk}))
    assert fetched.status_code == 200

    patched = api_client.patch(
        reverse(detail_url, kwargs={"id": pk}), {"name": "Changed"}, format="json"
    )
    assert patched.status_code == 200
    assert patched.json()["name"] == "Changed"

    deleted = api_client.delete(reverse(detail_url, kwargs={"id": pk}))
    assert deleted.status_code == 204
    assert model.objects.count() == 0


def test_duplicate_reference_name_is_rejected(api_client, inventory_tag):
    response = api_client.post(
        reverse("inventory:inventory-tags-list"), {"name": inventory_tag.name}, format="json"
    )

    assert response.status_code == 400
