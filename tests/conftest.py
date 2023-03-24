"""Shared fixtures.

Deliberately plain: no factory library, because the challenge brief forbids
adding packages. These build the smallest object graph each test needs and
nothing more.
"""

from __future__ import annotations

from datetime import date, timedelta

import pytest
from rest_framework.test import APIClient

from interview.inventory.models import Inventory, InventoryLanguage, InventoryTag, InventoryType
from interview.order.models import Order, OrderTag


@pytest.fixture
def api_client() -> APIClient:
    return APIClient()


@pytest.fixture
def language(db) -> InventoryLanguage:
    return InventoryLanguage.objects.create(name="English")


@pytest.fixture
def inventory_type(db) -> InventoryType:
    return InventoryType.objects.create(name="Movie")


@pytest.fixture
def inventory_tag(db) -> InventoryTag:
    return InventoryTag.objects.create(name="Action")


@pytest.fixture
def metadata() -> dict:
    return {
        "year": 1999,
        "actors": ["Keanu Reeves"],
        "imdb_rating": 8.7,
        "rotten_tomatoes_rating": 87,
        "film_locations": ["Sydney, Australia"],
    }


@pytest.fixture
def make_inventory(db, language, inventory_type, metadata):
    """Build inventory rows with sensible defaults."""

    def _make(name: str = "The Matrix", **overrides) -> Inventory:
        tags = overrides.pop("tags", None)
        inventory = Inventory.objects.create(
            name=name,
            language=overrides.pop("language", language),
            type=overrides.pop("type", inventory_type),
            metadata=overrides.pop("metadata", metadata),
            **overrides,
        )
        if tags:
            inventory.tags.set(tags)
        return inventory

    return _make


@pytest.fixture
def inventory(make_inventory, inventory_tag) -> Inventory:
    return make_inventory(tags=[inventory_tag])


@pytest.fixture
def order_tag(db) -> OrderTag:
    return OrderTag.objects.create(name="Dubbing")


@pytest.fixture
def make_order(db, make_inventory):
    """Build orders, defaulting to a window starting today."""

    counter = {"n": 0}

    def _make(
        *,
        start_date: date | None = None,
        embargo_date: date | None = None,
        inventory: Inventory | None = None,
        tags=(),
        is_active: bool = True,
    ) -> Order:
        counter["n"] += 1
        if inventory is None:
            inventory = make_inventory(name=f"Title {counter['n']}")
        today = date.today()
        order = Order.objects.create(
            inventory=inventory,
            start_date=start_date or today,
            embargo_date=embargo_date or today + timedelta(days=30),
            is_active=is_active,
        )
        if tags:
            order.tags.set(tags)
        return order

    return _make


@pytest.fixture
def order(make_order, order_tag) -> Order:
    return make_order(tags=[order_tag])
