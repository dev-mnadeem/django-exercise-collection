from django.db import models

from interview.core.behaviors import IsActiveModel, NameModel, TimestampedModel, UniqueNameModel


class InventoryTag(UniqueNameModel, TimestampedModel, IsActiveModel):
    class Meta:
        verbose_name_plural = "Inventory Tags"
        ordering = ("name",)

    def __str__(self) -> str:
        return self.name


class InventoryLanguage(UniqueNameModel, TimestampedModel):
    class Meta:
        verbose_name_plural = "Inventory Languages"
        ordering = ("name",)

    def __str__(self) -> str:
        return self.name


class InventoryType(UniqueNameModel, TimestampedModel):
    class Meta:
        verbose_name_plural = "Inventory Types"
        ordering = ("name",)

    def __str__(self) -> str:
        return self.name


class Inventory(NameModel, TimestampedModel):
    """A sellable piece of content.

    ``metadata`` is schema-less at the database level; the shape it must obey
    is enforced on the way in by ``interview.inventory.schemas``.
    """

    type = models.ForeignKey(
        InventoryType,
        on_delete=models.CASCADE,
        related_name="inventories",
    )
    language = models.ForeignKey(
        InventoryLanguage,
        on_delete=models.CASCADE,
        related_name="inventories",
    )
    tags = models.ManyToManyField(InventoryTag, related_name="inventories")
    metadata = models.JSONField(default=dict)

    class Meta:
        verbose_name_plural = "Inventories"
        ordering = ("-created_at", "id")

    def __str__(self) -> str:
        return self.name

    @classmethod
    def get_by_type(cls, type_id: int) -> models.QuerySet:
        return cls.objects.filter(type_id=type_id)

    @classmethod
    def get_by_language(cls, language_id: int) -> models.QuerySet:
        return cls.objects.filter(language_id=language_id)
