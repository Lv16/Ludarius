import hashlib
import logging

from django.contrib.auth.signals import user_logged_in, user_logged_out, user_login_failed
from django.dispatch import receiver

try:
    from allauth.account.signals import email_confirmed
except ImportError:  # pragma: no cover - allauth is installed in this project.
    email_confirmed = None


logger = logging.getLogger("security.audit")


def _client_ip(request) -> str:
    if request is None:
        return ""
    return request.META.get("REMOTE_ADDR", "")


def _request_path(request) -> str:
    if request is None:
        return ""
    return request.path


def _hash_value(value: str) -> str:
    if not value:
        return ""
    return hashlib.sha256(value.strip().lower().encode("utf-8")).hexdigest()


@receiver(user_logged_in)
def log_user_logged_in(sender, request, user, **kwargs):
    logger.info(
        "user_logged_in",
        extra={
            "event": "user_logged_in",
            "user_id": getattr(user, "pk", None),
            "client_ip": _client_ip(request),
            "request_path": _request_path(request),
        },
    )


@receiver(user_logged_out)
def log_user_logged_out(sender, request, user, **kwargs):
    logger.info(
        "user_logged_out",
        extra={
            "event": "user_logged_out",
            "user_id": getattr(user, "pk", None),
            "client_ip": _client_ip(request),
            "request_path": _request_path(request),
        },
    )


@receiver(user_login_failed)
def log_user_login_failed(sender, credentials, request, **kwargs):
    credentials = credentials or {}
    login_identifier = credentials.get("username") or credentials.get("email") or ""
    logger.warning(
        "user_login_failed",
        extra={
            "event": "user_login_failed",
            "login_identifier_hash": _hash_value(login_identifier),
            "client_ip": _client_ip(request),
            "request_path": _request_path(request),
        },
    )


if email_confirmed is not None:

    @receiver(email_confirmed)
    def log_email_confirmed(sender, request, email_address, **kwargs):
        user = getattr(email_address, "user", None)
        logger.info(
            "email_confirmed",
            extra={
                "event": "email_confirmed",
                "user_id": getattr(user, "pk", None),
                "client_ip": _client_ip(request),
                "request_path": _request_path(request),
            },
        )
