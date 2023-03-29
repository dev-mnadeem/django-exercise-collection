from django.urls import path

from interview.inventory.views import (
    InventoryCreatedAfterListView,
    InventoryLanguageListCreateView,
    InventoryLanguageRetrieveUpdateDestroyView,
    InventoryListCreateView,
    InventoryRetrieveUpdateDestroyView,
    InventoryTagListCreateView,
    InventoryTagRetrieveUpdateDestroyView,
    InventoryTypeListCreateView,
    InventoryTypeRetrieveUpdateDestroyView,
)

app_name = "inventory"

urlpatterns = [
    # Static segments first so they are never read as an inventory id.
    path("created-after/", InventoryCreatedAfterListView.as_view(), name="inventory-created-after"),
    path("languages/", InventoryLanguageListCreateView.as_view(), name="inventory-languages-list"),
    path(
        "languages/<int:id>/",
        InventoryLanguageRetrieveUpdateDestroyView.as_view(),
        name="inventory-languages-detail",
    ),
    path("tags/", InventoryTagListCreateView.as_view(), name="inventory-tags-list"),
    path(
        "tags/<int:id>/",
        InventoryTagRetrieveUpdateDestroyView.as_view(),
        name="inventory-tags-detail",
    ),
    path("types/", InventoryTypeListCreateView.as_view(), name="inventory-types-list"),
    path(
        "types/<int:id>/",
        InventoryTypeRetrieveUpdateDestroyView.as_view(),
        name="inventory-types-detail",
    ),
    path("<int:id>/", InventoryRetrieveUpdateDestroyView.as_view(), name="inventory-detail"),
    path("", InventoryListCreateView.as_view(), name="inventory-list"),
]
