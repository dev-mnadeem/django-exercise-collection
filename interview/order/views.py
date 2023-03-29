"""HTTP layer for the order app."""

from django.shortcuts import get_object_or_404
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView

from interview.order import selectors, services
from interview.order.models import Order, OrderTag
from interview.order.serializers import (
    OrderActivationSerializer,
    OrderSerializer,
    OrderTagSerializer,
    OrderWriteSerializer,
)


class OrderListCreateView(generics.ListCreateAPIView):
    """List orders (paginated), or create a new order."""

    def get_queryset(self):
        return selectors.order_queryset()

    def get_serializer_class(self):
        return OrderWriteSerializer if self.request.method == "POST" else OrderSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        order = services.create_order(**serializer.validated_data)
        return Response(OrderSerializer(order).data, status=status.HTTP_201_CREATED)


class OrderRetrieveView(generics.RetrieveAPIView):
    serializer_class = OrderSerializer
    lookup_field = "id"
    lookup_url_kwarg = "id"

    def get_queryset(self):
        return selectors.order_queryset()


class DeactivateOrderView(APIView):
    """Set the `is_active` state on an order.

    `POST` or `PATCH` with an empty body deactivates; `{"is_active": true}`
    reactivates. Modelled as an explicit action rather than a generic PATCH
    because "deactivate" is a domain operation, not a field assignment, and is
    the thing a caller wants to be able to retry safely.
    """

    def post(self, request, *args, **kwargs) -> Response:
        return self._set_state(request, kwargs["id"])

    def patch(self, request, *args, **kwargs) -> Response:
        return self._set_state(request, kwargs["id"])

    @staticmethod
    def _set_state(request, order_id: int) -> Response:
        order = get_object_or_404(selectors.order_queryset(), id=order_id)
        serializer = OrderActivationSerializer(data=request.data or {})
        serializer.is_valid(raise_exception=True)
        order = services.set_order_active(order, is_active=serializer.validated_data["is_active"])
        return Response(OrderSerializer(order).data, status=status.HTTP_200_OK)


class OrderDateRangeListView(generics.ListAPIView):
    """Orders whose window falls inside a requested window.

    `GET /orders/date-range/?start_date=YYYY-MM-DD&embargo_date=YYYY-MM-DD`
    """

    serializer_class = OrderSerializer

    def get_queryset(self):
        start_date, embargo_date = selectors.parse_window(self.request.query_params)
        return selectors.orders_in_window(start_date, embargo_date)


class OrderTagsListView(generics.ListAPIView):
    """Every tag attached to one order: `GET /orders/<id>/tags/`."""

    serializer_class = OrderTagSerializer

    def get_queryset(self):
        order = get_object_or_404(Order, id=self.kwargs["id"])
        return selectors.tags_for_order(order.id)


class OrdersByTagListView(generics.ListAPIView):
    """Every order carrying one tag: `GET /orders/tags/<id>/orders/`."""

    serializer_class = OrderSerializer

    def get_queryset(self):
        tag = get_object_or_404(OrderTag, id=self.kwargs["id"])
        return selectors.orders_for_tag(tag.id)


class OrderTagListCreateView(generics.ListCreateAPIView):
    serializer_class = OrderTagSerializer

    def get_queryset(self):
        return selectors.order_tag_queryset()


class OrderTagRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = OrderTagSerializer
    queryset = OrderTag.objects.all()
    lookup_field = "id"
    lookup_url_kwarg = "id"
    http_method_names = ["get", "patch", "delete", "head", "options"]
