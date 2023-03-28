"""Read-side queries for the order app."""

from __future__ import annotations

from datetime import date

from django.db.models import QuerySet

from interview.core.exceptions import InvalidFilterError
from interview.inventory.selectors import parse_date_param
from interview.order.models import Order, OrderTag


def order_queryset() -> QuerySet[Order]:
    """Every order, eager-loading exactly what ``OrderSerializer`` renders.

    ``OrderSerializer`` nests the full inventory item, which itself nests type,
    language and tags. Without this chain a 25-order page costs well over a
    hundred queries.
    """
    return (
        Order.objects.select_related("inventory", "inventory__type", "inventory__language")
        .prefetch_related("inventory__tags", "tags")
        .order_by("-start_date", "id")
    )


def orders_in_window(
    start_date: date,
    embargo_date: date,
    *,
    queryset: QuerySet[Order] | None = None,
) -> QuerySet[Order]:
    """Orders whose own window falls inside ``[start_date, embargo_date]``.

    Read as containment rather than overlap: an order qualifies when it both
    starts no earlier than the requested start and is embargoed no later than
    the requested embargo. Overlap semantics would need a different filter, so
    the choice is stated here rather than left to the reader.
    """
    if start_date > embargo_date:
        raise InvalidFilterError({"start_date": "start_date must be on or before embargo_date."})
    qs = order_queryset() if queryset is None else queryset
    return qs.filter(start_date__gte=start_date, embargo_date__lte=embargo_date)


def parse_window(params) -> tuple[date, date]:
    """Pull and validate the required ``start_date``/``embargo_date`` params."""
    start_date = parse_date_param(params.get("start_date"), field="start_date")
    embargo_date = parse_date_param(params.get("embargo_date"), field="embargo_date")

    missing = {
        name: "This query parameter is required."
        for name, value in (("start_date", start_date), ("embargo_date", embargo_date))
        if value is None
    }
    if missing:
        raise InvalidFilterError(missing)

    return start_date, embargo_date


def tags_for_order(order_id: int) -> QuerySet[OrderTag]:
    """Tags attached to one order."""
    return OrderTag.objects.filter(orders__id=order_id).order_by("name")


def orders_for_tag(tag_id: int) -> QuerySet[Order]:
    """Orders carrying one tag, eager-loaded for serialisation."""
    return order_queryset().filter(tags__id=tag_id)


def order_tag_queryset() -> QuerySet[OrderTag]:
    return OrderTag.objects.order_by("name")
