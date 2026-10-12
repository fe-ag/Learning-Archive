import os

from django.conf import settings
from django.core.exceptions import ValidationError


def validate_attachment(file):
    """Allow only known document types and enforce the configured size limit."""
    extension = os.path.splitext(file.name)[1].lstrip(".").lower()
    if extension not in settings.ALLOWED_ATTACHMENT_EXTENSIONS:
        allowed = ", ".join(settings.ALLOWED_ATTACHMENT_EXTENSIONS)
        raise ValidationError(
            "Files of type “.%(ext)s” are not allowed. Allowed types: %(allowed)s.",
            code="invalid_extension",
            params={"ext": extension, "allowed": allowed},
        )
    max_bytes = settings.MAX_UPLOAD_MB * 1024 * 1024
    if file.size > max_bytes:
        raise ValidationError(
            "This file is larger than %(limit)s MB.",
            code="file_too_large",
            params={"limit": settings.MAX_UPLOAD_MB},
        )
