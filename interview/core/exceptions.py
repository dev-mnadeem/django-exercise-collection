"""Exceptions raised by the service layer.

Services know nothing about HTTP. They raise these, and the views (or DRF's
handler) translate them into responses. That keeps the transport concern out
of the business rules and makes the services reusable from a management
command, a Celery task or a test.
"""

from rest_framework import status
from rest_framework.exceptions import APIException


class DomainError(APIException):
    """Base class for rule violations that map onto a 4xx response."""

    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "The request could not be processed."
    default_code = "domain_error"


class InvalidMetadataError(DomainError):
    """Inventory metadata failed schema validation."""

    default_detail = "Inventory metadata is invalid."
    default_code = "invalid_metadata"


class InvalidFilterError(DomainError):
    """A query-string filter was malformed."""

    default_detail = "One or more query parameters are invalid."
    default_code = "invalid_filter"
