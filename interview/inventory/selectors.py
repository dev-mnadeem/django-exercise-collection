"""Read-side queries for the inventory app.

Selectors return querysets. They are the only place that knows which related
rows a serializer will touch, which is why the eager-loading lives here rather
than being sprinkled across views: one `select_related`/`prefetch_related`
definition, reused by every caller.
"""

from __future__ import annotations

from datetime import date, datetime, time, timedelta, timezone as dt_timezone

from django.db.models import QuerySet
from django.utils import timezone

from interview.core.exceptions import InvalidFilterError
from interview.inventory.models import Inventory, InventoryLanguage, InventoryTag, InventoryType


def inventory_queryset() -> QuerySet[Inventory]:
    """Every inventory row, with the relations ``InventorySerializer`` reads.

    ``InventorySerializer`` nests type, language and tags. Without this the
    list endpoint issues 2N+1 queries; with it, four regardless of page size.
    """
    return (
        Inventory.objects.select_related("type", "language")
        .prefetch_related("tags")
        .order_by("-created_at", "id")
    )


def parse_date_param(raw: str | None, *, field: str) -> date | None:
    """Parse an ISO-8601 date (or datetime) query parameter.

    Returns ``None`` when the parameter is absent. Raises
    ``InvalidFilterError`` rather than letting a ``ValueError`` become a 500.
    """
    if raw is None or not raw.strip():
        return None
    value = raw.strip()
    try:
        return date.fromisoformat(value)
    except ValueError:
        pass
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).date()
    except ValueError as exc:
        raise InvalidFilterError(
            {field: f"Expected an ISO-8601 date such as 2023-03-24, got {raw!r}."}
        ) from exc


def inventory_created_after(after: date, *, queryset: QuerySet[Inventory] | None = None):
    """Inventory created strictly after the end of the given day.

    "After a certain day" is read as *after that whole day*, so passing
    2023-03-24 excludes anything created during the 24th itself. The boundary
    is made explicit here instead of being implied by a `__gt` on a date.
    """
    qs = inventory_queryset() if queryset is None else queryset
    start_of_next_day = datetime.combine(after, time.min) + timedelta(days=1)
    if timezone.is_naive(start_of_next_day):
        start_of_next_day = start_of_next_day.replace(tzinfo=dt_timezone.utc)
    return qs.filter(created_at__gte=start_of_next_day)


def filtered_inventory(params) -> QuerySet[Inventory]:
    """Apply the supported query-string filters to the inventory list."""
    qs = inventory_queryset()

    created_after = parse_date_param(params.get("created_after"), field="created_after")
    if created_after is not None:
        qs = inventory_created_after(created_after, queryset=qs)

    type_id = params.get("type")
    if type_id:
        qs = qs.filter(type_id=type_id)

    language_id = params.get("language")
    if language_id:
        qs = qs.filter(language_id=language_id)

    return qs


def inventory_tag_queryset() -> QuerySet[InventoryTag]:
    return InventoryTag.objects.order_by("name")


def inventory_language_queryset() -> QuerySet[InventoryLanguage]:
    return InventoryLanguage.objects.order_by("name")


def inventory_type_queryset() -> QuerySet[InventoryType]:
    return InventoryType.objects.order_by("name")
