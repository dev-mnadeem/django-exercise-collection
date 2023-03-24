"""N+1 regression guards.

Both serializers nest relations. Without the eager loading in the selectors
the query count grows with the page size; these tests fail if someone drops a
`select_related`/`prefetch_related` while refactoring.
"""

import pytest
from django.test.utils import CaptureQueriesContext
from django.db import connection
from django.urls import reverse

pytestmark = pytest.mark.django_db


def _query_count(client, url, params=None) -> int:
    with CaptureQueriesContext(connection) as captured:
        response = client.get(url, params or {})
        assert response.status_code == 200
    return len(captured)


def test_inventory_list_query_count_is_independent_of_page_size(
    api_client, make_inventory, inventory_tag
):
    for index in range(12):
        make_inventory(name=f"Title {index}", tags=[inventory_tag])

    url = reverse("inventory:inventory-list")
    small = _query_count(api_client, url, {"limit": 2})
    large = _query_count(api_client, url, {"limit": 12})

    assert small == large, f"{small} queries for 2 rows vs {large} for 12 -- N+1 reintroduced"
    assert large <= 4


def test_order_list_query_count_is_independent_of_page_size(
    api_client, make_order, order_tag, inventory_tag
):
    for _ in range(12):
        make_order(tags=[order_tag])

    url = reverse("order:order-list")
    small = _query_count(api_client, url, {"limit": 2})
    large = _query_count(api_client, url, {"limit": 12})

    assert small == large, f"{small} queries for 2 rows vs {large} for 12 -- N+1 reintroduced"
    assert large <= 6
