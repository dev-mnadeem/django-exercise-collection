"""Every route resolves to the view it claims to."""

import pytest
from django.urls import resolve, reverse

from interview.inventory import views as inventory_views
from interview.order import views as order_views


@pytest.mark.parametrize(
    "name,kwargs,view",
    [
        ("inventory:inventory-list", {}, inventory_views.InventoryListCreateView),
        ("inventory:inventory-created-after", {}, inventory_views.InventoryCreatedAfterListView),
        (
            "inventory:inventory-detail",
            {"id": 1},
            inventory_views.InventoryRetrieveUpdateDestroyView,
        ),
        ("inventory:inventory-tags-list", {}, inventory_views.InventoryTagListCreateView),
        ("inventory:inventory-languages-list", {}, inventory_views.InventoryLanguageListCreateView),
        ("inventory:inventory-types-list", {}, inventory_views.InventoryTypeListCreateView),
        ("order:order-list", {}, order_views.OrderListCreateView),
        ("order:order-detail", {"id": 1}, order_views.OrderRetrieveView),
        ("order:order-deactivate", {"id": 1}, order_views.DeactivateOrderView),
        ("order:order-date-range", {}, order_views.OrderDateRangeListView),
        ("order:order-tags", {"id": 1}, order_views.OrderTagsListView),
        ("order:orders-by-tag", {"id": 1}, order_views.OrdersByTagListView),
        ("order:order-tags-list", {}, order_views.OrderTagListCreateView),
    ],
)
def test_route_resolves_to_its_view(name, kwargs, view):
    match = resolve(reverse(name, kwargs=kwargs))

    assert match.func.cls is view


def test_static_segments_win_over_the_id_pattern():
    """`/orders/tags/` must not be read as order id "tags"."""
    assert resolve("/orders/tags/").func.cls is order_views.OrderTagListCreateView
    assert resolve("/orders/date-range/").func.cls is order_views.OrderDateRangeListView
    assert resolve("/inventory/created-after/").func.cls is (
        inventory_views.InventoryCreatedAfterListView
    )
