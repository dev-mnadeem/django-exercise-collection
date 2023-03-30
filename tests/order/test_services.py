"""Order write rules."""

from datetime import date, timedelta

import pytest

from interview.core.exceptions import DomainError
from interview.order import services
from interview.order.models import Order

pytestmark = pytest.mark.django_db


def test_deactivate_order(order):
    services.deactivate_order(order)

    order.refresh_from_db()
    assert order.is_active is False


def test_activate_order(make_order):
    order = make_order(is_active=False)

    services.activate_order(order)

    order.refresh_from_db()
    assert order.is_active is True


def test_deactivating_twice_is_a_no_op(order):
    services.deactivate_order(order)
    services.deactivate_order(order)

    order.refresh_from_db()
    assert order.is_active is False


def test_create_order(inventory, order_tag):
    today = date.today()

    order = services.create_order(
        inventory=inventory,
        start_date=today,
        embargo_date=today + timedelta(days=10),
        tags=[order_tag],
    )

    assert Order.objects.count() == 1
    assert list(order.tags.all()) == [order_tag]


def test_create_order_rejects_an_embargo_before_the_start(inventory):
    today = date.today()

    with pytest.raises(DomainError):
        services.create_order(
            inventory=inventory,
            start_date=today,
            embargo_date=today - timedelta(days=1),
        )

    assert Order.objects.count() == 0
