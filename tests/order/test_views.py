"""The order HTTP surface, including the four challenge endpoints."""

from datetime import date, timedelta

import pytest
from django.urls import reverse

from interview.order.models import Order, OrderTag

pytestmark = pytest.mark.django_db


def test_list_orders(api_client, order):
    response = api_client.get(reverse("order:order-list"))

    assert response.status_code == 200
    body = response.json()
    assert body["count"] == 1
    assert body["results"][0]["inventory"]["name"] == order.inventory.name


def test_create_order(api_client, inventory, order_tag):
    today = date.today()

    response = api_client.post(
        reverse("order:order-list"),
        {
            "inventory": inventory.id,
            "start_date": today.isoformat(),
            "embargo_date": (today + timedelta(days=10)).isoformat(),
            "tags": [order_tag.id],
        },
        format="json",
    )

    assert response.status_code == 201, response.data
    assert response.json()["inventory"]["name"] == inventory.name
    assert Order.objects.count() == 1


def test_create_order_rejects_a_backwards_window(api_client, inventory):
    today = date.today()

    response = api_client.post(
        reverse("order:order-list"),
        {
            "inventory": inventory.id,
            "start_date": today.isoformat(),
            "embargo_date": (today - timedelta(days=1)).isoformat(),
        },
        format="json",
    )

    assert response.status_code == 400
    assert Order.objects.count() == 0


def test_retrieve_order(api_client, order):
    response = api_client.get(reverse("order:order-detail", kwargs={"id": order.id}))

    assert response.status_code == 200
    assert response.json()["id"] == order.id


def test_retrieve_missing_order_is_404(api_client):
    assert api_client.get(reverse("order:order-detail", kwargs={"id": 999999})).status_code == 404


# --- Challenge 2: DeactivateOrderView ------------------------------------


def test_deactivate_endpoint_sets_is_active_false(api_client, order):
    response = api_client.post(reverse("order:order-deactivate", kwargs={"id": order.id}))

    assert response.status_code == 200, response.data
    assert response.json()["is_active"] is False
    order.refresh_from_db()
    assert order.is_active is False


def test_deactivate_endpoint_can_reactivate(api_client, make_order):
    order = make_order(is_active=False)

    response = api_client.post(
        reverse("order:order-deactivate", kwargs={"id": order.id}),
        {"is_active": True},
        format="json",
    )

    assert response.status_code == 200
    order.refresh_from_db()
    assert order.is_active is True


def test_deactivate_endpoint_accepts_patch(api_client, order):
    response = api_client.patch(reverse("order:order-deactivate", kwargs={"id": order.id}))

    assert response.status_code == 200
    order.refresh_from_db()
    assert order.is_active is False


def test_deactivate_endpoint_is_idempotent(api_client, order):
    url = reverse("order:order-deactivate", kwargs={"id": order.id})

    assert api_client.post(url).status_code == 200
    assert api_client.post(url).status_code == 200

    order.refresh_from_db()
    assert order.is_active is False


def test_deactivate_missing_order_is_404(api_client):
    response = api_client.post(reverse("order:order-deactivate", kwargs={"id": 999999}))

    assert response.status_code == 404


def test_deactivate_leaves_other_orders_alone(api_client, make_order):
    target = make_order()
    bystander = make_order()

    api_client.post(reverse("order:order-deactivate", kwargs={"id": target.id}))

    bystander.refresh_from_db()
    assert bystander.is_active is True


# --- Challenge 3: orders within a start/embargo window --------------------


def test_date_range_endpoint(api_client, make_order):
    today = date.today()
    inside = make_order(
        start_date=today + timedelta(days=1), embargo_date=today + timedelta(days=9)
    )
    make_order(start_date=today - timedelta(days=9), embargo_date=today + timedelta(days=9))

    response = api_client.get(
        reverse("order:order-date-range"),
        {
            "start_date": today.isoformat(),
            "embargo_date": (today + timedelta(days=10)).isoformat(),
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["count"] == 1
    assert body["results"][0]["id"] == inside.id


def test_date_range_requires_both_parameters(api_client):
    response = api_client.get(
        reverse("order:order-date-range"), {"start_date": date.today().isoformat()}
    )

    assert response.status_code == 400
    assert "embargo_date" in response.json()


def test_date_range_rejects_a_malformed_date(api_client):
    response = api_client.get(
        reverse("order:order-date-range"),
        {"start_date": "not-a-date", "embargo_date": "2024-01-01"},
    )

    assert response.status_code == 400


def test_date_range_rejects_an_inverted_window(api_client):
    today = date.today()

    response = api_client.get(
        reverse("order:order-date-range"),
        {
            "start_date": (today + timedelta(days=10)).isoformat(),
            "embargo_date": today.isoformat(),
        },
    )

    assert response.status_code == 400


# --- Challenge 6: tags on an order ----------------------------------------


def test_tags_for_order_endpoint(api_client, order, order_tag):
    response = api_client.get(reverse("order:order-tags", kwargs={"id": order.id}))

    assert response.status_code == 200
    body = response.json()
    assert [tag["name"] for tag in body["results"]] == [order_tag.name]


def test_tags_for_order_on_a_missing_order_is_404(api_client):
    response = api_client.get(reverse("order:order-tags", kwargs={"id": 999999}))

    assert response.status_code == 404


def test_tags_for_order_is_empty_when_untagged(api_client, make_order):
    untagged = make_order()

    response = api_client.get(reverse("order:order-tags", kwargs={"id": untagged.id}))

    assert response.status_code == 200
    assert response.json()["count"] == 0


# --- Challenge 7: orders on a tag -----------------------------------------


def test_orders_for_tag_endpoint(api_client, make_order, order_tag):
    other_tag = OrderTag.objects.create(name="Subbing")
    tagged = make_order(tags=[order_tag])
    make_order(tags=[other_tag])

    response = api_client.get(reverse("order:orders-by-tag", kwargs={"id": order_tag.id}))

    assert response.status_code == 200
    body = response.json()
    assert body["count"] == 1
    assert body["results"][0]["id"] == tagged.id


def test_orders_for_tag_on_a_missing_tag_is_404(api_client):
    response = api_client.get(reverse("order:orders-by-tag", kwargs={"id": 999999}))

    assert response.status_code == 404


def test_order_tag_crud(api_client):
    created = api_client.post(
        reverse("order:order-tags-list"), {"name": "Mastering"}, format="json"
    )
    assert created.status_code == 201
    pk = created.json()["id"]

    assert api_client.get(reverse("order:order-tags-detail", kwargs={"id": pk})).status_code == 200
    assert (
        api_client.delete(reverse("order:order-tags-detail", kwargs={"id": pk})).status_code == 204
    )
    assert OrderTag.objects.count() == 0
