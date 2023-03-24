from django.urls import path

from interview.order.views import (
    DeactivateOrderView,
    OrderDateRangeListView,
    OrderListCreateView,
    OrderRetrieveView,
    OrderTagListCreateView,
    OrderTagRetrieveUpdateDestroyView,
    OrderTagsListView,
    OrdersByTagListView,
)

app_name = "order"

urlpatterns = [
    # Static segments first so that "tags" and "date-range" are never read as
    # an order id.
    path("date-range/", OrderDateRangeListView.as_view(), name="order-date-range"),
    path("tags/", OrderTagListCreateView.as_view(), name="order-tags-list"),
    path("tags/<int:id>/", OrderTagRetrieveUpdateDestroyView.as_view(), name="order-tags-detail"),
    path("tags/<int:id>/orders/", OrdersByTagListView.as_view(), name="orders-by-tag"),
    path("<int:id>/tags/", OrderTagsListView.as_view(), name="order-tags"),
    path("<int:id>/deactivate/", DeactivateOrderView.as_view(), name="order-deactivate"),
    path("<int:id>/", OrderRetrieveView.as_view(), name="order-detail"),
    path("", OrderListCreateView.as_view(), name="order-list"),
]
