"""The project's user model.

``UserProfile`` replaces ``django.contrib.auth.models.User`` as
``AUTH_USER_MODEL``. It authenticates on the email address rather than a
separate username, which is what the rest of the system actually keys on.
"""

from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.utils import timezone


class UserProfileManager(BaseUserManager):
    """Creates users keyed on a normalised email address."""

    use_in_migrations = True

    def _create_user(self, email: str, password: str | None, **extra_fields):
        if not email:
            raise ValueError("An email address is required.")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        # set_password hashes; never assign to `password` directly.
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email: str, password: str | None = None, **extra_fields):
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email: str, password: str | None = None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        if extra_fields.get("is_staff") is not True:
            raise ValueError("A superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("A superuser must have is_superuser=True.")
        return self._create_user(email, password, **extra_fields)


def avatar_upload_to(instance: "UserProfile", filename: str) -> str:
    """Namespace avatars per user so filenames cannot collide."""
    return f"avatars/{instance.pk or 'new'}/{filename}"


class UserProfile(AbstractBaseUser, PermissionsMixin):
    """A person who can sign in.

    ``AbstractBaseUser`` supplies ``password`` and ``last_login``;
    ``PermissionsMixin`` supplies ``is_superuser`` plus the group and
    permission relations.
    """

    email = models.EmailField(unique=True, db_index=True)
    username = models.CharField(max_length=150, blank=True)
    first_name = models.CharField(max_length=150, blank=True)
    last_name = models.CharField(max_length=150, blank=True)
    avatar = models.ImageField(upload_to=avatar_upload_to, blank=True, null=True)

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(default=timezone.now)

    objects = UserProfileManager()

    USERNAME_FIELD = "email"
    EMAIL_FIELD = "email"
    REQUIRED_FIELDS: list[str] = []

    class Meta:
        verbose_name = "User Profile"
        verbose_name_plural = "User Profiles"
        ordering = ("email",)

    def __str__(self) -> str:
        return self.email

    def save(self, *args, **kwargs):
        # The email is the credential, so keep the display username in step
        # with it unless one was supplied explicitly.
        if not self.username:
            self.username = self.email
        super().save(*args, **kwargs)

    def get_full_name(self) -> str:
        """Full name, falling back to the email when no name is recorded."""
        full_name = f"{self.first_name} {self.last_name}".strip()
        return full_name or self.email

    def get_short_name(self) -> str:
        return self.first_name or self.email

    def get_username(self) -> str:
        """The value this user authenticates with, i.e. the email address."""
        return self.email

    @property
    def is_admin(self) -> bool:
        """Alias kept for readability; superusers are the administrators.

        Stored separately it would be a second source of truth that could
        disagree with ``is_superuser``, so it is derived instead.
        """
        return self.is_superuser
