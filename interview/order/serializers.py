"""Wire-format (de)serialisation for the order app.

Same read/write split as the inventory app: reads nest the inventory item for
the client's convenience, writes take primary keys.
"""

from rest_framework import serializers

from interview.inventory.models import Inventory
from interview.inventory.serializers import InventorySerializer
from interview.order.models import Order, OrderTag


class OrderTagSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderTag
        fields = ["id", "name", "is_active"]


class OrderSerializer(serializers.ModelSerializer):
    """Read representation: inventory and tags expanded inline."""

    inventory = InventorySerializer(read_only=True)
    tags = OrderTagSerializer(many=True, read_only=True)

    class Meta:
        model = Order
        fields = ["id", "inventory", "start_date", "embargo_date", "tags", "is_active"]
        read_only_fields = fields


class OrderWriteSerializer(serializers.ModelSerializer):
    """Write representation: relations given as primary keys."""

    inventory = serializers.PrimaryKeyRelatedField(queryset=Inventory.objects.all())
    tags = serializers.PrimaryKeyRelatedField(
        queryset=OrderTag.objects.all(), many=True, required=False
    )

    class Meta:
        model = Order
        fields = ["inventory", "start_date", "embargo_date", "tags", "is_active"]


class OrderActivationSerializer(serializers.Serializer):
    """Body of a request that flips an order's activation flag.

    ``is_active`` is optional and defaults to ``False`` so that
    ``POST /orders/<id>/deactivate/`` with an empty body does the obvious
    thing, while an explicit ``{"is_active": true}`` reactivates.
    """

    is_active = serializers.BooleanField(required=False, default=False)
