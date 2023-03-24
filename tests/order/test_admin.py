"""The bulk activation actions on the order changelist."""

from datetime import timedelta

import pytest
from django.contrib.admin.sites import site
from django.contrib.messages.storage.fallback import FallbackStorage
from django.test import RequestFactory

from interview.order.models import Order

pytestmark = pytest.mark.django_db


@pytest.fixture
def admin_request():
    request = RequestFactory().post("/admin/order/order/")
    request.session = {}
    request._messages = FallbackStorage(request)
    return request


def test_deactivate_action_flips_the_flag_and_moves_updated_at(make_order, admin_request):
    orders = [make_order(), make_order()]
    stale = orders[0].updated_at - timedelta(days=1)
    Order.objects.update(updated_at=stale)

    site._registry[Order].deactivate_selected(admin_request, Order.objects.all())

    for order in Order.objects.all():
        assert order.is_active is False
        assert order.updated_at > stale


def test_activate_action(make_order, admin_request):
    make_order(is_active=False)

    site._registry[Order].activate_selected(admin_request, Order.objects.all())

    assert Order.objects.get().is_active is True
