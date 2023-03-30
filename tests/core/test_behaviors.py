"""Regression tests for the abstract model behaviours.

``IsActiveModel.activate`` used to set ``is_active=False`` and ``deactivate``
used to set it ``True`` -- each was wired to the other's value. Nothing caught
it because nothing called them. These tests pin the semantics down.
"""

import uuid

import pytest

from interview.core.behaviors import UUIDModel
from interview.order.models import Order


@pytest.mark.django_db
def test_deactivate_sets_is_active_false(order: Order):
    assert order.is_active is True

    Order.deactivate(order.pk)
    order.refresh_from_db()

    assert order.is_active is False


@pytest.mark.django_db
def test_activate_sets_is_active_true(make_order):
    order = make_order(is_active=False)

    Order.activate(order.pk)
    order.refresh_from_db()

    assert order.is_active is True


@pytest.mark.django_db
def test_set_active_reports_rows_touched(order: Order):
    assert Order.set_active(order.pk, is_active=False) == 1
    assert Order.set_active(pk=-1, is_active=False) == 0


@pytest.mark.django_db
def test_set_active_only_touches_the_named_row(make_order):
    target = make_order()
    bystander = make_order()

    Order.set_active(target.pk, is_active=False)

    target.refresh_from_db()
    bystander.refresh_from_db()
    assert target.is_active is False
    assert bystander.is_active is True


def test_uuid_model_generates_its_own_primary_key():
    """The field used to have no default, so every insert raised."""
    field = UUIDModel._meta.get_field("uuid")

    assert field.default is uuid.uuid4
    assert field.primary_key is True
    assert field.editable is False


@pytest.mark.django_db
def test_unique_name_lookup_returns_none_when_absent(inventory_tag):
    from interview.inventory.models import InventoryTag

    assert InventoryTag.get_by_name("Action") == inventory_tag
    assert InventoryTag.get_by_name("Nonexistent") is None
