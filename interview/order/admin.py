from django.contrib import admin

from interview.order.models import Order, OrderTag


@admin.register(OrderTag)
class OrderTagAdmin(admin.ModelAdmin):
    list_display = ("name", "is_active", "created_at")
    list_filter = ("is_active",)
    search_fields = ("name",)


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("id", "inventory", "start_date", "embargo_date", "is_active")
    list_filter = ("is_active", "tags", "start_date")
    search_fields = ("inventory__name",)
    autocomplete_fields = ("inventory", "tags")
    readonly_fields = ("created_at", "updated_at")
    date_hierarchy = "start_date"
    actions = ("deactivate_selected", "activate_selected")

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("inventory")

    @admin.action(description="Deactivate selected orders")
    def deactivate_selected(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f"{updated} order(s) deactivated.")

    @admin.action(description="Activate selected orders")
    def activate_selected(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f"{updated} order(s) activated.")
