"""The swapped-in user model."""

import pytest
from django.conf import settings
from django.contrib.auth import get_user_model

UserProfile = get_user_model()

pytestmark = pytest.mark.django_db


def test_it_is_the_projects_user_model():
    assert settings.AUTH_USER_MODEL == "profiles.UserProfile"
    assert UserProfile._meta.label == "profiles.UserProfile"


def test_it_authenticates_on_email():
    assert UserProfile.USERNAME_FIELD == "email"
    assert UserProfile.REQUIRED_FIELDS == []


def test_create_user_hashes_the_password():
    user = UserProfile.objects.create_user(email="a@example.com", password="s3cret-pass-phrase")

    assert user.password != "s3cret-pass-phrase"
    assert user.check_password("s3cret-pass-phrase")


def test_create_user_normalises_the_email_domain():
    user = UserProfile.objects.create_user(email="Person@EXAMPLE.COM", password="x")

    assert user.email == "Person@example.com"


def test_create_user_requires_an_email():
    with pytest.raises(ValueError):
        UserProfile.objects.create_user(email="", password="x")


def test_email_is_unique():
    from django.db import IntegrityError

    UserProfile.objects.create_user(email="a@example.com", password="x")

    with pytest.raises(IntegrityError):
        UserProfile.objects.create_user(email="a@example.com", password="y")


def test_create_superuser():
    admin = UserProfile.objects.create_superuser(email="root@example.com", password="x")

    assert admin.is_staff is True
    assert admin.is_superuser is True
    assert admin.is_admin is True


def test_create_superuser_refuses_contradictory_flags():
    with pytest.raises(ValueError):
        UserProfile.objects.create_superuser(email="root@example.com", password="x", is_staff=False)


def test_get_full_name():
    user = UserProfile.objects.create_user(
        email="a@example.com", password="x", first_name="Ada", last_name="Lovelace"
    )

    assert user.get_full_name() == "Ada Lovelace"
    assert user.get_short_name() == "Ada"


def test_get_full_name_falls_back_to_the_email():
    user = UserProfile.objects.create_user(email="a@example.com", password="x")

    assert user.get_full_name() == "a@example.com"


def test_get_username_returns_the_email():
    user = UserProfile.objects.create_user(email="a@example.com", password="x")

    assert user.get_username() == "a@example.com"
    assert user.username == "a@example.com"


def test_an_explicit_username_is_preserved():
    user = UserProfile.objects.create_user(email="a@example.com", password="x", username="ada")

    assert user.username == "ada"
    assert user.get_username() == "a@example.com"


def test_is_authenticated_is_a_property_as_django_requires():
    """The brief asked for `is_authenticated()`; Django defines it as a
    property and its own middleware reads it as one. Keeping Django's
    contract is what makes `request.user.is_authenticated` work."""
    user = UserProfile.objects.create_user(email="a@example.com", password="x")

    assert user.is_authenticated is True
    assert isinstance(UserProfile.is_authenticated, property)


def test_authentication_backend_accepts_the_email():
    from django.contrib.auth import authenticate

    UserProfile.objects.create_user(email="a@example.com", password="correct-horse-battery")

    assert authenticate(username="a@example.com", password="correct-horse-battery") is not None
    assert authenticate(username="a@example.com", password="wrong") is None


def test_avatar_is_optional():
    user = UserProfile.objects.create_user(email="a@example.com", password="x")

    assert not user.avatar
