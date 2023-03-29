"""HTTP layer for the inventory app.

Views do three things and nothing else: deserialise, delegate to a
service/selector, serialise. Anything resembling a business rule lives in
``services.py``; anything resembling a query lives in ``selectors.py``.
"""

from rest_framework import generics, status
from rest_framework.response import Response

from interview.core.pagination import InventoryLimitOffsetPagination
from interview.inventory import selectors, services
from interview.inventory.models import Inventory, InventoryLanguage, InventoryTag, InventoryType
from interview.inventory.serializers import (
    InventoryLanguageSerializer,
    InventorySerializer,
    InventoryTagSerializer,
    InventoryTypeSerializer,
    InventoryWriteSerializer,
)


class InventoryListCreateView(generics.ListCreateAPIView):
    """List inventory (paginated), or create a new item.

    Filters: `created_after=YYYY-MM-DD`, `type=<id>`, `language=<id>`.
    Pages three items at a time via `limit` and `offset`.
    """

    pagination_class = InventoryLimitOffsetPagination

    def get_queryset(self):
        return selectors.filtered_inventory(self.request.query_params)

    def get_serializer_class(self):
        return InventoryWriteSerializer if self.request.method == "POST" else InventorySerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        inventory = services.create_inventory(**serializer.validated_data)
        # Echo the full read representation, not the sparse write one.
        return Response(InventorySerializer(inventory).data, status=status.HTTP_201_CREATED)


class InventoryCreatedAfterListView(generics.ListAPIView):
    """Inventory created after a given day: `?created_after=YYYY-MM-DD`.

    A dedicated endpoint for the common "what is new since ..." question. It
    shares its selector with the main list, so the date semantics can only be
    defined in one place.
    """

    serializer_class = InventorySerializer
    pagination_class = InventoryLimitOffsetPagination

    def get_queryset(self):
        after = selectors.parse_date_param(
            self.request.query_params.get("created_after"), field="created_after"
        )
        if after is None:
            return selectors.inventory_queryset()
        return selectors.inventory_created_after(after)


class InventoryRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, patch or delete one inventory item. Missing ids give a 404."""

    lookup_field = "id"
    lookup_url_kwarg = "id"
    http_method_names = ["get", "patch", "delete", "head", "options"]

    def get_queryset(self):
        return selectors.inventory_queryset()

    def get_serializer_class(self):
        return InventoryWriteSerializer if self.request.method == "PATCH" else InventorySerializer

    def perform_destroy(self, instance: Inventory):
        services.delete_inventory(instance)

    def update(self, request, *args, **kwargs):
        inventory = self.get_object()
        serializer = self.get_serializer(inventory, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        inventory = services.update_inventory(inventory, **serializer.validated_data)
        return Response(InventorySerializer(inventory).data, status=status.HTTP_200_OK)


class InventoryTagListCreateView(generics.ListCreateAPIView):
    serializer_class = InventoryTagSerializer

    def get_queryset(self):
        return selectors.inventory_tag_queryset()


class InventoryTagRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = InventoryTagSerializer
    queryset = InventoryTag.objects.all()
    lookup_field = "id"
    lookup_url_kwarg = "id"
    http_method_names = ["get", "patch", "delete", "head", "options"]


class InventoryLanguageListCreateView(generics.ListCreateAPIView):
    serializer_class = InventoryLanguageSerializer

    def get_queryset(self):
        return selectors.inventory_language_queryset()


class InventoryLanguageRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = InventoryLanguageSerializer
    queryset = InventoryLanguage.objects.all()
    lookup_field = "id"
    lookup_url_kwarg = "id"
    http_method_names = ["get", "patch", "delete", "head", "options"]


class InventoryTypeListCreateView(generics.ListCreateAPIView):
    serializer_class = InventoryTypeSerializer

    def get_queryset(self):
        return selectors.inventory_type_queryset()


class InventoryTypeRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = InventoryTypeSerializer
    queryset = InventoryType.objects.all()
    lookup_field = "id"
    lookup_url_kwarg = "id"
    http_method_names = ["get", "patch", "delete", "head", "options"]
