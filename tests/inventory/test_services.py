"""Inventory write rules, exercised without going through HTTP."""

import pytest

from interview.core.exceptions import InvalidMetadataError
from interview.inventory import services
from interview.inventory.models import Inventory


@pytest.mark.django_db
def test_create_inventory_persists_and_normalises_metadata(
    language, inventory_type, inventory_tag, metadata
):
    inventory = services.create_inventory(
        name="The Matrix",
        type=inventory_type,
        language=language,
        metadata=metadata,
        tags=[inventory_tag],
    )

    inventory.refresh_from_db()
    assert inventory.pk is not None
    assert list(inventory.tags.all()) == [inventory_tag]
    assert inventory.metadata["imdb_rating"] == 8.7


@pytest.mark.django_db
def test_create_inventory_rejects_bad_metadata(language, inventory_type):
    with pytest.raises(InvalidMetadataError):
        services.create_inventory(
            name="Broken",
            type=inventory_type,
            language=language,
            metadata={"year": "not a year"},
        )

    assert Inventory.objects.count() == 0


@pytest.mark.django_db
def test_create_inventory_leaves_no_partial_row_behind(language, inventory_type):
    """Validation happens before the insert, so nothing is written."""
    with pytest.raises(InvalidMetadataError):
        services.create_inventory(
            name="Broken",
            type=inventory_type,
            language=language,
            metadata={},
        )

    assert not Inventory.objects.filter(name="Broken").exists()


@pytest.mark.django_db
def test_update_inventory_revalidates_metadata(inventory, metadata):
    services.update_inventory(inventory, metadata={**metadata, "year": 2003})
    inventory.refresh_from_db()
    assert inventory.metadata["year"] == 2003

    with pytest.raises(InvalidMetadataError):
        services.update_inventory(inventory, metadata={"nonsense": True})


@pytest.mark.django_db
def test_update_inventory_replaces_tags(inventory, inventory_tag):
    from interview.inventory.models import InventoryTag

    drama = InventoryTag.objects.create(name="Drama")

    services.update_inventory(inventory, tags=[drama])

    assert list(inventory.tags.all()) == [drama]


@pytest.mark.django_db
def test_update_inventory_renames(inventory):
    services.update_inventory(inventory, name="Renamed")

    inventory.refresh_from_db()
    assert inventory.name == "Renamed"


@pytest.mark.django_db
def test_delete_inventory(inventory):
    services.delete_inventory(inventory)

    assert Inventory.objects.count() == 0
