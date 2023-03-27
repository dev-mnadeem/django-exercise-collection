"""Reusable abstract model behaviours.

Each class adds one orthogonal capability. Concrete models compose the ones
they need instead of inheriting a single fat base class.
"""

import uuid

from django.core.exceptions import ObjectDoesNotExist
from django.db import models


class UUIDModel(models.Model):
    """Primary key is a client-opaque UUID rather than a guessable integer."""

    uuid = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        unique=True,
    )

    class Meta:
        abstract = True

    @classmethod
    def get_by_id(cls, uuid: str):
        try:
            return cls.objects.get(uuid=uuid)
        except ObjectDoesNotExist:
            return None


class TimestampedModel(models.Model):
    """Adds indexed creation and modification stamps."""

    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class IsActiveModel(models.Model):
    """Adds a soft-activation flag plus helpers to flip it."""

    # Deliberately not indexed on its own: a two-valued column has too little
    # selectivity to help. Where it matters it appears as the leading column of
    # a composite index on the concrete model (see ``Order.Meta.indexes``).
    is_active = models.BooleanField(default=True)

    class Meta:
        abstract = True

    @classmethod
    def set_active(cls, pk: int, *, is_active: bool) -> int:
        """Set ``is_active`` on one row. Returns the number of rows updated."""
        return cls.objects.filter(pk=pk).update(is_active=is_active)

    @classmethod
    def activate(cls, pk: int) -> int:
        return cls.set_active(pk, is_active=True)

    @classmethod
    def deactivate(cls, pk: int) -> int:
        return cls.set_active(pk, is_active=False)


class NameModel(models.Model):
    """Adds a non-unique, indexed display name."""

    name = models.CharField(max_length=255, db_index=True)

    class Meta:
        abstract = True

    @classmethod
    def get_by_name(cls, name: str) -> models.QuerySet:
        return cls.objects.filter(name=name)


class UniqueNameModel(models.Model):
    """Adds a unique display name used as a natural key."""

    name = models.CharField(max_length=255, unique=True)

    class Meta:
        abstract = True

    @classmethod
    def get_by_name(cls, name: str):
        try:
            return cls.objects.get(name=name)
        except ObjectDoesNotExist:
            return None
