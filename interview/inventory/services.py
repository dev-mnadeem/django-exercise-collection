"""Write-side business rules for the inventory app.

Services take already-deserialised Python values, apply the rules, and return
model instances. They raise ``DomainError`` subclasses rather than returning
``Response`` objects, so nothing here imports the HTTP layer and every one of
these functions is callable from a management command or a test.
"""

from __future__ import annotations

import logging

from django.db import transaction

from interview.inventory.models import Inventory, InventoryType
from interview.inventory.schemas import metadata_registry

logger = logging.getLogger(__name__)


def _type_name(inventory_type: InventoryType | None) -> str | None:
    return inventory_type.name if inventory_type is not None else None


@transaction.atomic
def create_inventory(
    *,
    name: str,
    type: InventoryType,
    language,
    metadata: dict,
    tags=(),
) -> Inventory:
    """Create one inventory item, validating its metadata against the schema
    registered for its type.

    Wrapped in a transaction because the tags are attached after the insert;
    a failure part-way through would otherwise leave an untagged row behind.
    """
    validated_metadata = metadata_registry.validate(_type_name(type), metadata)

    inventory = Inventory.objects.create(
        name=name,
        type=type,
        language=language,
        metadata=validated_metadata,
    )
    if tags:
        inventory.tags.set(tags)

    logger.info("Created inventory %s (%s)", inventory.pk, inventory.name)
    return inventory


@transaction.atomic
def update_inventory(inventory: Inventory, **fields) -> Inventory:
    """Partially update an inventory item.

    Metadata, when supplied, is re-validated against the schema for the item's
    (possibly new) type rather than being written through blindly.
    """
    tags = fields.pop("tags", None)

    if "metadata" in fields:
        inventory_type = fields.get("type", inventory.type)
        fields["metadata"] = metadata_registry.validate(
            _type_name(inventory_type), fields["metadata"]
        )

    for field, value in fields.items():
        setattr(inventory, field, value)

    if fields:
        inventory.save(update_fields=[*fields, "updated_at"])
    if tags is not None:
        inventory.tags.set(tags)

    logger.info("Updated inventory %s", inventory.pk)
    return inventory


def delete_inventory(inventory: Inventory) -> None:
    logger.info("Deleted inventory %s (%s)", inventory.pk, inventory.name)
    inventory.delete()
