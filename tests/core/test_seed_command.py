"""The seed command replaced a script that could only ever run once."""

import pytest
from django.core.management import call_command

from interview.inventory.models import Inventory, InventoryLanguage, InventoryType
from interview.order.models import Order


@pytest.mark.django_db
def test_seed_populates_the_fixture():
    call_command("seed_demo_data", verbosity=0)

    assert InventoryLanguage.objects.count() == 150
    assert InventoryType.objects.count() == 3
    assert Inventory.objects.count() == 17
    assert Order.objects.count() == 5


@pytest.mark.django_db
def test_seed_is_idempotent():
    call_command("seed_demo_data", verbosity=0)
    call_command("seed_demo_data", verbosity=0)

    assert Inventory.objects.count() == 17
    assert Order.objects.count() == 5


@pytest.mark.django_db
def test_seed_metadata_validates_against_the_registry():
    """The original fixture shipped a `rotten_toamtoes_rating` typo."""
    from interview.inventory.schemas import metadata_registry

    call_command("seed_demo_data", verbosity=0)

    for item in Inventory.objects.select_related("type"):
        metadata_registry.validate(item.type.name, item.metadata)


@pytest.mark.django_db
def test_seeded_orders_have_a_coherent_window():
    """The original fixture shipped an order embargoed before it started."""
    call_command("seed_demo_data", verbosity=0)

    for order in Order.objects.all():
        assert order.start_date <= order.embargo_date, f"order {order.pk} has an inverted window"
