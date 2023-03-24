from django.contrib import admin

from interview.inventory.models import Inventory, InventoryLanguage, InventoryTag, InventoryType


@admin.register(InventoryTag)
class InventoryTagAdmin(admin.ModelAdmin):
    list_display = ("name", "is_active", "created_at")
    list_filter = ("is_active",)
    search_fields = ("name",)


@admin.register(InventoryLanguage)
class InventoryLanguageAdmin(admin.ModelAdmin):
    list_display = ("name", "created_at")
    search_fields = ("name",)


@admin.register(InventoryType)
class InventoryTypeAdmin(admin.ModelAdmin):
    list_display = ("name", "created_at")
    search_fields = ("name",)


@admin.register(Inventory)
class InventoryAdmin(admin.ModelAdmin):
    list_display = ("name", "type", "language", "created_at")
    list_filter = ("type", "language", "tags")
    search_fields = ("name",)
    autocomplete_fields = ("type", "language", "tags")
    readonly_fields = ("created_at", "updated_at")
    date_hierarchy = "created_at"

    def get_queryset(self, request):
        # The changelist renders type and language for every row.
        return super().get_queryset(request).select_related("type", "language")
