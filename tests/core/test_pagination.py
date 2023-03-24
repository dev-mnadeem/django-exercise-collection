"""The pagination defaults that the rest of the suite relies on."""

from django.test import override_settings

from interview.core.pagination import DefaultLimitOffsetPagination, InventoryLimitOffsetPagination


def test_default_pagination_is_offset_limit_with_a_ceiling():
    paginator = DefaultLimitOffsetPagination()

    assert paginator.limit_query_param == "limit"
    assert paginator.offset_query_param == "offset"
    assert paginator.default_limit == 25
    assert paginator.max_limit == 100


def test_inventory_pagination_defaults_to_three():
    assert InventoryLimitOffsetPagination().default_limit == 3


@override_settings(INVENTORY_PAGE_SIZE=7)
def test_inventory_page_size_is_configurable():
    assert InventoryLimitOffsetPagination().default_limit == 7
