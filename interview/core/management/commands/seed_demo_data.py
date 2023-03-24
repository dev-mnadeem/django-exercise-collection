"""Load the demo fixture.

Replaces the original `echo "from database import *" | python manage.py shell`
incantation. That script ran on import, inserted unconditionally, and so blew
up on a unique constraint the second time anyone ran it. This command is
idempotent: run it as often as you like.
"""

from __future__ import annotations

from datetime import timedelta

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from interview.core import seed_data
from interview.inventory.models import Inventory, InventoryLanguage, InventoryTag, InventoryType
from interview.order.models import Order, OrderTag


class Command(BaseCommand):
    help = "Populate the database with the demo inventory and order fixture."

    def add_arguments(self, parser) -> None:
        parser.add_argument(
            "--flush",
            action="store_true",
            help="Delete existing inventory and order rows before seeding.",
        )

    @transaction.atomic
    def handle(self, *args, **options) -> None:
        if options["flush"]:
            Order.objects.all().delete()
            Inventory.objects.all().delete()
            OrderTag.objects.all().delete()
            InventoryTag.objects.all().delete()
            InventoryType.objects.all().delete()
            InventoryLanguage.objects.all().delete()
            self.stdout.write("Cleared existing inventory and order data.")

        languages = self._bulk_get_or_create(InventoryLanguage, seed_data.LANGUAGES)
        types = self._bulk_get_or_create(InventoryType, seed_data.INVENTORY_TYPES)
        inventory_tags = self._bulk_get_or_create(InventoryTag, seed_data.INVENTORY_TAGS)
        order_tags = self._bulk_get_or_create(OrderTag, seed_data.ORDER_TAGS)

        inventories: dict[str, Inventory] = {}
        for item in seed_data.INVENTORY_ITEMS:
            inventory, _ = Inventory.objects.update_or_create(
                name=item["name"],
                defaults={
                    "language": languages[item["language"]],
                    "type": types[item["type"]],
                    "metadata": item["metadata"],
                },
            )
            inventory.tags.set(inventory_tags[name] for name in item["tags"])
            inventories[item["name"]] = inventory

        today = timezone.now().date()
        for spec in seed_data.ORDERS:
            order, _ = Order.objects.update_or_create(
                inventory=inventories[spec["inventory"]],
                start_date=today + timedelta(days=spec["start_offset_days"]),
                defaults={
                    "embargo_date": today + timedelta(days=spec["embargo_offset_days"]),
                    "is_active": spec["is_active"],
                },
            )
            order.tags.set(order_tags[name] for name in spec["tags"])

        self.stdout.write(
            self.style.SUCCESS(
                f"Seeded {len(languages)} languages, {len(types)} types, "
                f"{len(inventory_tags)} inventory tags, {len(order_tags)} order tags, "
                f"{len(inventories)} inventory items and {len(seed_data.ORDERS)} orders."
            )
        )

    @staticmethod
    def _bulk_get_or_create(model, names) -> dict:
        """Ensure a row exists per name and return them keyed by name."""
        existing = {obj.name: obj for obj in model.objects.filter(name__in=names)}
        missing = [model(name=name) for name in names if name not in existing]
        if missing:
            model.objects.bulk_create(missing)
            existing = {obj.name: obj for obj in model.objects.filter(name__in=names)}
        return existing
