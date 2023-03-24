"""Schema registry for the untyped ``Inventory.metadata`` JSON column.

``metadata`` is a ``JSONField``, so the database will accept literally
anything. That is convenient until two teams disagree about whether the key is
``imdb_rating`` or ``imdbRating`` and nobody notices for a month. (This
repository already shipped one such typo: the seed row for *The Fellowship of
the Ring* stored ``rotten_toamtoes_rating``.)

This module is the seam that stops it. One schema is registered per inventory
type name; validation happens on the way in. Adding a type-specific shape is a
two-line change and requires touching neither the service nor the view:

    from pydantic import BaseModel
    from interview.inventory.metadata import metadata_registry

    class EpisodeMetadata(InventoryMetaData):
        season: int
        episode: int

    metadata_registry.register("Episode", EpisodeMetadata)

Anything not explicitly registered validates against the default schema.
"""

from __future__ import annotations

import json
from decimal import Decimal
from typing import Type

from pydantic import BaseModel, ValidationError

from interview.core.exceptions import InvalidMetadataError


class InventoryMetaData(BaseModel):
    """Default shape for inventory metadata.

    ``film_locations`` defaults to an empty list so that rows written before
    the field existed continue to validate.
    """

    year: int
    actors: list[str]
    imdb_rating: Decimal
    rotten_tomatoes_rating: int
    film_locations: list[str] = []

    class Config:
        extra = "forbid"


class MetadataSchemaRegistry:
    """Maps an inventory type name to the schema its metadata must satisfy."""

    def __init__(self, default: Type[BaseModel]) -> None:
        self._default = default
        self._schemas: dict[str, Type[BaseModel]] = {}

    def register(self, type_name: str, schema: Type[BaseModel]) -> None:
        """Bind ``schema`` to an inventory type, by name, case-insensitively."""
        self._schemas[type_name.casefold()] = schema

    def schema_for(self, type_name: str | None) -> Type[BaseModel]:
        if not type_name:
            return self._default
        return self._schemas.get(type_name.casefold(), self._default)

    def registered_types(self) -> list[str]:
        return sorted(self._schemas)

    def validate(self, type_name: str | None, payload: object) -> dict:
        """Validate ``payload`` and return a JSON-serialisable dict.

        Raises ``InvalidMetadataError`` (a 400) on a bad payload.
        """
        if not isinstance(payload, dict):
            raise InvalidMetadataError({"metadata": "Expected an object."})

        schema = self.schema_for(type_name)
        try:
            model = schema(**payload)
        except ValidationError as exc:
            raise InvalidMetadataError({"metadata": exc.errors()}) from exc
        except TypeError as exc:
            raise InvalidMetadataError({"metadata": str(exc)}) from exc

        # Round-trip through pydantic's JSON encoder. ``.dict()`` alone leaves
        # a Decimal in place, which ``JSONField`` cannot store -- the original
        # cause of every POST /inventory/ returning 400.
        return json.loads(model.json())


metadata_registry = MetadataSchemaRegistry(default=InventoryMetaData)
