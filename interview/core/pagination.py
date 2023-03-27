"""Offset/limit pagination classes.

Every list endpoint is paginated. An unbounded list endpoint is fine against
seed data and a liability against production data, so the default is applied
project-wide in ``REST_FRAMEWORK`` rather than opted into per view.
"""

from django.conf import settings
from rest_framework.pagination import LimitOffsetPagination


class DefaultLimitOffsetPagination(LimitOffsetPagination):
    """Project-wide default: offset/limit with a hard ceiling."""

    default_limit = 25
    max_limit = 100
    limit_query_param = "limit"
    offset_query_param = "offset"


class InventoryLimitOffsetPagination(DefaultLimitOffsetPagination):
    """Inventory listings page three items at a time by default."""

    @property
    def default_limit(self) -> int:
        return getattr(settings, "INVENTORY_PAGE_SIZE", 3)
