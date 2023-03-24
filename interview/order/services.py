"""Write-side business rules for the order app."""

from __future__ import annotations

import logging

from django.db import transaction

from interview.core.exceptions import DomainError
from interview.order.models import Order

logger = logging.getLogger(__name__)


@transaction.atomic
def set_order_active(order: Order, *, is_active: bool) -> Order:
    """Set an order's activation flag and return the refreshed instance.

    Idempotent: re-deactivating an inactive order is a no-op success, not an
    error, so a retried request cannot fail spuriously.
    """
    if order.is_active != is_active:
        Order.set_active(order.pk, is_active=is_active)
        order.refresh_from_db(fields=["is_active", "updated_at"])
        logger.info("Order %s is_active -> %s", order.pk, is_active)
    return order


def deactivate_order(order: Order) -> Order:
    return set_order_active(order, is_active=False)


def activate_order(order: Order) -> Order:
    return set_order_active(order, is_active=True)


@transaction.atomic
def create_order(*, inventory, start_date, embargo_date, tags=(), is_active: bool = True) -> Order:
    """Create one order, rejecting an embargo that precedes its start."""
    if embargo_date < start_date:
        raise DomainError({"embargo_date": "embargo_date must not precede start_date."})

    order = Order.objects.create(
        inventory=inventory,
        start_date=start_date,
        embargo_date=embargo_date,
        is_active=is_active,
    )
    if tags:
        order.tags.set(tags)

    logger.info("Created order %s for inventory %s", order.pk, inventory.pk)
    return order
