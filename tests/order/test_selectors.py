"""Order query behaviour, including the date-window semantics."""

from datetime import date, timedelta

import pytest

from interview.core.exceptions import InvalidFilterError
from interview.order import selectors

pytestmark = pytest.mark.django_db


def test_window_is_containment_not_overlap(make_order):
    today = date.today()
    inside = make_order(
        start_date=today + timedelta(days=2), embargo_date=today + timedelta(days=8)
    )
    make_order(start_date=today - timedelta(days=5), embargo_date=today + timedelta(days=8))
    make_order(start_date=today + timedelta(days=2), embargo_date=today + timedelta(days=40))

    found = selectors.orders_in_window(today, today + timedelta(days=10))

    assert list(found) == [inside]


def test_window_boundaries_are_inclusive(make_order):
    today = date.today()
    edge = make_order(start_date=today, embargo_date=today + timedelta(days=10))

    found = selectors.orders_in_window(today, today + timedelta(days=10))

    assert list(found) == [edge]


def test_inverted_window_is_rejected():
    today = date.today()

    with pytest.raises(InvalidFilterError):
        selectors.orders_in_window(today + timedelta(days=5), today)


def test_parse_window_requires_both_parameters():
    with pytest.raises(InvalidFilterError):
        selectors.parse_window({"start_date": "2023-01-01"})

    with pytest.raises(InvalidFilterError):
        selectors.parse_window({})


def test_parse_window_returns_dates():
    start, embargo = selectors.parse_window(
        {"start_date": "2023-01-01", "embargo_date": "2023-02-01"}
    )

    assert (start, embargo) == (date(2023, 1, 1), date(2023, 2, 1))


def test_tags_for_order(order, order_tag):
    assert list(selectors.tags_for_order(order.id)) == [order_tag]


def test_tags_for_order_is_scoped_to_that_order(make_order, order_tag):
    from interview.order.models import OrderTag

    other_tag = OrderTag.objects.create(name="Subbing")
    mine = make_order(tags=[order_tag])
    make_order(tags=[other_tag])

    assert list(selectors.tags_for_order(mine.id)) == [order_tag]


def test_orders_for_tag(make_order, order_tag):
    from interview.order.models import OrderTag

    other_tag = OrderTag.objects.create(name="Subbing")
    tagged = make_order(tags=[order_tag])
    make_order(tags=[other_tag])

    assert list(selectors.orders_for_tag(order_tag.id)) == [tagged]
