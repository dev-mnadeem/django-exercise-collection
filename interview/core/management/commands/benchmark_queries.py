"""Measure the cost of serialising a page of inventory and of orders, with
and without the eager loading defined in the selectors.

This exists so that the N+1 claim in the README is a number somebody measured
rather than an assertion. Run it against a throwaway database:

    ./manage.py benchmark_queries --rows 200 --page-size 25
"""

from __future__ import annotations

import time
from datetime import date, timedelta

from django.core.management.base import BaseCommand
from django.db import connection, transaction
from django.test.utils import CaptureQueriesContext

from interview.inventory.models import Inventory, InventoryLanguage, InventoryTag, InventoryType
from interview.inventory.selectors import inventory_queryset
from interview.inventory.serializers import InventorySerializer
from interview.order.models import Order, OrderTag
from interview.order.selectors import order_queryset
from interview.order.serializers import OrderSerializer


class Command(BaseCommand):
    help = "Measure query counts for the inventory and order list endpoints."

    def add_arguments(self, parser) -> None:
        parser.add_argument("--rows", type=int, default=200, help="Rows to generate.")
        parser.add_argument("--page-size", type=int, default=25, help="Rows per page.")
        parser.add_argument(
            "--keep",
            action="store_true",
            help="Keep the generated rows instead of rolling them back.",
        )

    def handle(self, *args, **options) -> None:
        rows = options["rows"]
        page_size = options["page_size"]

        if options["keep"]:
            self._run(rows, page_size)
            return

        # Generate, measure, then roll the whole lot back.
        try:
            with transaction.atomic():
                self._run(rows, page_size)
                raise _Rollback()
        except _Rollback:
            self.stdout.write("Benchmark rows rolled back.")

    def _run(self, rows: int, page_size: int) -> None:
        self._generate(rows)

        self.stdout.write(f"rows={rows} page_size={page_size} vendor={connection.vendor}")
        self.stdout.write("")
        self.stdout.write(f"{'endpoint':<22}{'eager':<8}{'queries':>9}{'ms':>10}")
        self.stdout.write("-" * 49)

        cases = [
            ("GET /inventory/", True, inventory_queryset, InventorySerializer),
            (
                "GET /inventory/",
                False,
                lambda: Inventory.objects.order_by("-created_at", "id"),
                InventorySerializer,
            ),
            ("GET /orders/", True, order_queryset, OrderSerializer),
            (
                "GET /orders/",
                False,
                lambda: Order.objects.order_by("-start_date", "id"),
                OrderSerializer,
            ),
        ]

        for label, eager, queryset_factory, serializer_class in cases:
            queries, elapsed_ms = self._measure(queryset_factory, serializer_class, page_size)
            self.stdout.write(
                f"{label:<22}{'yes' if eager else 'no':<8}{queries:>9}{elapsed_ms:>10.1f}"
            )

    @staticmethod
    def _measure(queryset_factory, serializer_class, page_size: int) -> tuple[int, float]:
        # Warm any connection-level setup so it is not charged to the first case.
        list(queryset_factory()[:1])

        started = time.perf_counter()
        with CaptureQueriesContext(connection) as captured:
            page = list(queryset_factory()[:page_size])
            serializer_class(page, many=True).data
        elapsed_ms = (time.perf_counter() - started) * 1000
        return len(captured), elapsed_ms

    def _generate(self, rows: int) -> None:
        language, _ = InventoryLanguage.objects.get_or_create(name="Benchmark Language")
        inventory_type, _ = InventoryType.objects.get_or_create(name="Benchmark Type")
        tags = [
            InventoryTag.objects.get_or_create(name=f"Benchmark Tag {index}")[0]
            for index in range(3)
        ]
        order_tags = [
            OrderTag.objects.get_or_create(name=f"Benchmark Order Tag {index}")[0]
            for index in range(3)
        ]

        metadata = {
            "year": 2001,
            "actors": ["A. Actor", "B. Actor"],
            "imdb_rating": 7.5,
            "rotten_tomatoes_rating": 80,
            "film_locations": ["Somewhere"],
        }
        inventories = Inventory.objects.bulk_create(
            Inventory(
                name=f"Benchmark Title {index}",
                language=language,
                type=inventory_type,
                metadata=metadata,
            )
            for index in range(rows)
        )
        # bulk_create does not populate m2m; attach through the join table.
        through = Inventory.tags.through
        through.objects.bulk_create(
            through(inventory_id=inventory.pk, inventorytag_id=tag.pk)
            for inventory in inventories
            for tag in tags
        )

        today = date.today()
        orders = Order.objects.bulk_create(
            Order(
                inventory=inventory,
                start_date=today,
                embargo_date=today + timedelta(days=30),
            )
            for inventory in inventories
        )
        order_through = Order.tags.through
        order_through.objects.bulk_create(
            order_through(order_id=order.pk, ordertag_id=tag.pk)
            for order in orders
            for tag in order_tags
        )


class _Rollback(Exception):
    """Signals the benchmark transaction to unwind."""
