"""Wire-format (de)serialisation for the inventory app.

Read and write are separate classes on purpose. A single serializer that nests
``InventoryTypeSerializer()`` for output is, on input, demanding a full nested
object that ``ModelSerializer`` cannot write anyway -- which is why every
``POST /inventory/`` used to fail with "Expected a dictionary, but got int".
Reads nest for the client's convenience; writes take primary keys.
"""

from rest_framework import serializers

from interview.inventory.models import Inventory, InventoryLanguage, InventoryTag, InventoryType


class InventoryTagSerializer(serializers.ModelSerializer):
    class Meta:
        model = InventoryTag
        fields = ["id", "name", "is_active"]


class InventoryLanguageSerializer(serializers.ModelSerializer):
    class Meta:
        model = InventoryLanguage
        fields = ["id", "name"]


class InventoryTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = InventoryType
        fields = ["id", "name"]


class InventorySerializer(serializers.ModelSerializer):
    """Read representation: relations expanded inline."""

    type = InventoryTypeSerializer(read_only=True)
    language = InventoryLanguageSerializer(read_only=True)
    tags = InventoryTagSerializer(many=True, read_only=True)

    class Meta:
        model = Inventory
        fields = ["id", "name", "type", "language", "tags", "metadata", "created_at"]
        read_only_fields = fields


class InventoryWriteSerializer(serializers.ModelSerializer):
    """Write representation: relations given as primary keys.

    ``metadata`` is declared as a plain ``DictField`` -- the real validation is
    the pydantic schema applied by the service layer, and duplicating it here
    would give two places to keep in step.
    """

    type = serializers.PrimaryKeyRelatedField(queryset=InventoryType.objects.all())
    language = serializers.PrimaryKeyRelatedField(queryset=InventoryLanguage.objects.all())
    tags = serializers.PrimaryKeyRelatedField(
        queryset=InventoryTag.objects.all(), many=True, required=False
    )
    metadata = serializers.DictField()

    class Meta:
        model = Inventory
        fields = ["name", "type", "language", "tags", "metadata"]
