"""Inventory query behaviour, including the date-boundary semantics."""

from datetime import date, datetime, timezone

import pytest

from interview.core.exceptions import InvalidFilterError
from interview.inventory import selectors


def test_parse_date_param_accepts_a_plain_date():
    assert selectors.parse_date_param("2023-03-24", field="d") == date(2023, 3, 24)


def test_parse_date_param_accepts_an_iso_datetime():
    assert selectors.parse_date_param("2023-03-24T12:30:00Z", field="d") == date(2023, 3, 24)


def test_parse_date_param_returns_none_when_absent():
    assert selectors.parse_date_param(None, field="d") is None
    assert selectors.parse_date_param("   ", field="d") is None


@pytest.mark.parametrize("raw", ["yesterday", "24-03-2023", "2023-13-01", ""])
def test_parse_date_param_rejects_junk(raw):
    if raw == "":
        assert selectors.parse_date_param(raw, field="d") is None
        return
    with pytest.raises(InvalidFilterError):
        selectors.parse_date_param(raw, field="d")


@pytest.mark.django_db
def test_created_after_excludes_the_named_day_itself(make_inventory):
    """ "After a certain day" means after that whole day, not after midnight."""
    same_day = make_inventory(name="Same day")
    next_day = make_inventory(name="Next day")

    cutoff = date(2023, 3, 24)
    _set_created_at(same_day, datetime(2023, 3, 24, 23, 59, tzinfo=timezone.utc))
    _set_created_at(next_day, datetime(2023, 3, 25, 0, 1, tzinfo=timezone.utc))

    names = set(selectors.inventory_created_after(cutoff).values_list("name", flat=True))

    assert names == {"Next day"}


@pytest.mark.django_db
def test_created_after_includes_everything_later(make_inventory):
    item = make_inventory(name="Much later")
    _set_created_at(item, datetime(2024, 1, 1, tzinfo=timezone.utc))

    assert selectors.inventory_created_after(date(2023, 3, 24)).count() == 1


@pytest.mark.django_db
def test_filtered_inventory_without_params_returns_everything(make_inventory):
    make_inventory(name="A")
    make_inventory(name="B")

    assert selectors.filtered_inventory({}).count() == 2


@pytest.mark.django_db
def test_filtered_inventory_narrows_by_type(make_inventory, inventory_type):
    from interview.inventory.models import InventoryType

    other = InventoryType.objects.create(name="Episode")
    make_inventory(name="A")
    make_inventory(name="B", type=other)

    assert selectors.filtered_inventory({"type": other.id}).count() == 1


def _set_created_at(instance, when: datetime) -> None:
    """`auto_now_add` ignores assignment, so write the column directly."""
    type(instance).objects.filter(pk=instance.pk).update(created_at=when)
