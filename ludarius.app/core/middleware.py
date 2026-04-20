import hashlib
import ipaddress
import logging

from django.conf import settings
from django.core.cache import cache
from django.http import HttpResponse, HttpResponseNotFound


logger = logging.getLogger(__name__)


class SecurityHeadersMiddleware:
    CSP_POLICY = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline'; "
        "style-src 'self' 'unsafe-inline'; "
        "img-src 'self' data: https:; "
        "font-src 'self' data:; "
        "connect-src 'self'; "
        "object-src 'none'; "
        "base-uri 'self'; "
        "frame-ancestors 'none'; "
        "form-action 'self'"
    )

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        self._set_header_if_missing(response, "Referrer-Policy", "same-origin")
        self._set_header_if_missing(response, "Cross-Origin-Opener-Policy", "same-origin")
        self._set_header_if_missing(response, "Permissions-Policy", "camera=(), microphone=(), geolocation=(), payment=()")
        self._set_header_if_missing(response, "X-Content-Type-Options", "nosniff")

        if settings.SECURITY_CSP_ENABLED:
            csp_header = (
                "Content-Security-Policy-Report-Only"
                if settings.SECURITY_CSP_REPORT_ONLY
                else "Content-Security-Policy"
            )
            self._set_header_if_missing(response, csp_header, self.CSP_POLICY)

        return response

    def _set_header_if_missing(self, response, header: str, value: str):
        if not response.has_header(header):
            response[header] = value


class PrivateNoStoreMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        self.admin_path = f"/{settings.ADMIN_URL.strip('/')}/"
        self.static_path = settings.STATIC_URL if settings.STATIC_URL.startswith("/") else "/static/"
        self.private_prefixes = (self.admin_path, "/accounts/")

    def __call__(self, request):
        response = self.get_response(request)
        if self._should_skip(request):
            return response

        if self._is_private_request(request):
            response["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0, private"
            response["Pragma"] = "no-cache"
            response["Expires"] = "0"

        return response

    def _should_skip(self, request) -> bool:
        return request.path.startswith(self.static_path)

    def _is_private_request(self, request) -> bool:
        if request.path.startswith(self.private_prefixes):
            return True

        user = getattr(request, "user", None)
        return bool(user and user.is_authenticated)


class AdminSecurityMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        self.admin_path = f"/{settings.ADMIN_URL.strip('/')}/"
        self.admin_login_path = f"{self.admin_path}login/"
        self.allowed_networks = self._parse_allowed_networks(settings.ADMIN_ALLOWED_IPS)

    def __call__(self, request):
        if not request.path.startswith(self.admin_path):
            return self.get_response(request)

        client_ip = self._client_ip(request)
        if self.allowed_networks and not self._ip_allowed(client_ip):
            logger.warning("Blocked admin access from disallowed IP", extra={"client_ip": client_ip})
            return HttpResponseNotFound()

        if self._is_admin_login_post(request):
            cache_key = self._rate_limit_key(request, client_ip)
            if cache.get(cache_key, 0) >= settings.ADMIN_LOGIN_RATE_LIMIT:
                logger.warning("Blocked admin login due to rate limit", extra={"client_ip": client_ip})
                return HttpResponse("Too many login attempts.", status=429)

            response = self.get_response(request)
            if response.status_code == 200:
                attempts = cache.get(cache_key, 0) + 1
                cache.set(cache_key, attempts, settings.ADMIN_LOGIN_RATE_TIMEOUT)
            elif 300 <= response.status_code < 400:
                cache.delete(cache_key)
            return response

        return self.get_response(request)

    def _is_admin_login_post(self, request) -> bool:
        return request.method == "POST" and request.path == self.admin_login_path

    def _client_ip(self, request) -> str:
        forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR", "")
        if settings.ADMIN_TRUST_X_FORWARDED_FOR and forwarded_for:
            return forwarded_for.split(",", 1)[0].strip()
        return request.META.get("REMOTE_ADDR", "")

    def _rate_limit_key(self, request, client_ip: str) -> str:
        username = (request.POST.get("username") or "").strip().lower()
        raw_key = f"{client_ip}:{username}"
        digest = hashlib.sha256(raw_key.encode("utf-8")).hexdigest()
        return f"admin-login-attempts:{digest}"

    def _parse_allowed_networks(self, raw_values: list[str]):
        networks = []
        for value in raw_values:
            try:
                networks.append(ipaddress.ip_network(value, strict=False))
            except ValueError:
                logger.warning("Ignoring invalid ADMIN_ALLOWED_IPS entry", extra={"entry": value})
        return networks

    def _ip_allowed(self, client_ip: str) -> bool:
        try:
            ip = ipaddress.ip_address(client_ip)
        except ValueError:
            return False
        return any(ip in network for network in self.allowed_networks)
