"""The metadata schema registry: the seam that types an untyped JSON column."""

import pytest
from pydantic import BaseModel

from interview.core.exceptions import InvalidMetadataError
from interview.inventory.schemas import (
    InventoryMetaData,
    MetadataSchemaRegistry,
    metadata_registry,
)


@pytest.fixture
def valid_payload() -> dict:
    return {
        "year": 1999,
        "actors": ["Keanu Reeves"],
        "imdb_rating": 8.7,
        "rotten_tomatoes_rating": 87,
    }


def test_film_locations_defaults_to_empty(valid_payload):
    """Rows written before the field existed must keep validating."""
    result = metadata_registry.validate("Movie", valid_payload)

    assert result["film_locations"] == []


def test_validated_metadata_is_json_serialisable(valid_payload):
    """The Decimal that `.dict()` leaves behind is what JSONField rejects."""
    import json

    result = metadata_registry.validate("Movie", valid_payload)

    assert isinstance(result["imdb_rating"], float)
    json.dumps(result)  # must not raise


def test_misspelled_key_is_rejected(valid_payload):
    payload = {**valid_payload}
    payload.pop("rotten_tomatoes_rating")
    payload["rotten_toamtoes_rating"] = 91

    with pytest.raises(InvalidMetadataError):
        metadata_registry.validate("Movie", payload)


def test_missing_required_field_is_rejected(valid_payload):
    payload = {k: v for k, v in valid_payload.items() if k != "year"}

    with pytest.raises(InvalidMetadataError):
        metadata_registry.validate("Movie", payload)


def test_wrong_type_is_rejected(valid_payload):
    with pytest.raises(InvalidMetadataError):
        metadata_registry.validate("Movie", {**valid_payload, "actors": "Keanu Reeves"})


def test_non_object_payload_is_rejected():
    with pytest.raises(InvalidMetadataError):
        metadata_registry.validate("Movie", ["not", "an", "object"])


def test_unregistered_type_falls_back_to_the_default_schema():
    registry = MetadataSchemaRegistry(default=InventoryMetaData)

    assert registry.schema_for("Anything At All") is InventoryMetaData
    assert registry.schema_for(None) is InventoryMetaData


def test_a_type_specific_schema_can_be_registered(valid_payload):
    """The extension point: one call, no change to services or views."""

    class EpisodeMetadata(InventoryMetaData):
        season: int
        episode: int

    registry = MetadataSchemaRegistry(default=InventoryMetaData)
    registry.register("Episode", EpisodeMetadata)

    assert registry.schema_for("Episode") is EpisodeMetadata
    assert registry.registered_types() == ["episode"]

    # The default schema is still what an unregistered type gets.
    assert registry.schema_for("Movie") is InventoryMetaData

    with pytest.raises(InvalidMetadataError):
        registry.validate("Episode", valid_payload)  # missing season/episode

    result = registry.validate("Episode", {**valid_payload, "season": 1, "episode": 2})
    assert result["season"] == 1


def test_registration_is_case_insensitive():
    class Other(BaseModel):
        pass

    registry = MetadataSchemaRegistry(default=InventoryMetaData)
    registry.register("Episode", Other)

    assert registry.schema_for("EPISODE") is Other
    assert registry.schema_for("episode") is Other
