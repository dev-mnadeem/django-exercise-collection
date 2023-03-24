from django.db import models

from interview.core.behaviors import IsActiveModel, TimestampedModel, UniqueNameModel
from interview.inventory.models import Inventory


class OrderTag(UniqueNameModel, TimestampedModel, IsActiveModel):
    class Meta:
        verbose_name_plural = "Order Tags"
        ordering = ("name",)

    def __str__(self) -> str:
        return self.name


class Order(TimestampedModel, IsActiveModel):
    inventory = models.ForeignKey(
        Inventory,
        on_delete=models.CASCADE,
        related_name="orders",
    )
    start_date = models.DateField(db_index=True)
    embargo_date = models.DateField(db_index=True)
    tags = models.ManyToManyField(OrderTag, related_name="orders")

    class Meta:
        ordering = ("-start_date", "id")
        indexes = [
            # Serves the "orders in a window" endpoint, which filters on both
            # date columns at once; a pair of single-column indexes would make
            # the planner choose one and then re-check the other.
            models.Index(fields=["start_date", "embargo_date"], name="order_window_idx"),
            # Serves the common "active orders, most recent first" listing.
            models.Index(fields=["is_active", "-start_date"], name="order_active_start_idx"),
        ]

    def __str__(self) -> str:
        return f"{self.inventory.name} - {self.start_date}"
