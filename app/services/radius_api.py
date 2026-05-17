from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


logger = logging.getLogger("hobehub.radius_api")


class RadiusApiError(Exception):
    pass


@dataclass
class RadiusApiConfig:
    base_url: str
    master_api_key: str
    username: str
    password: str
    api_enabled: bool = True

    @property
    def login_url(self) -> str:
        return f"{self.base_url.rstrip('/')}/login"

    def endpoint_url(self, endpoint: str) -> str:
        return f"{self.base_url.rstrip('/')}/{endpoint.lstrip('/')}"


def mask_sensitive_data(value: Any):
    if isinstance(value, dict):
        return {
            key: (
                "***"
                if any(token in key.lower() for token in ("password", "api_key", "token", "secret", "adv_auth"))
                else mask_sensitive_data(item)
            )
            for key, item in value.items()
        }
    if isinstance(value, list):
        return [mask_sensitive_data(item) for item in value]
    return value


def _debug_enabled() -> bool:
    return os.getenv("RADIUS_API_DEBUG", "").strip().lower() in {"1", "true", "yes", "on"}


def _debug_log(channel: str, url: str, payload: dict | None, headers: dict | None, status_code: int | None = None, response_body: str | None = None):
    if not _debug_enabled():
        return
    body_preview = response_body or ""
    if len(body_preview) > 500:
        body_preview = body_preview[:500] + "..."
    logger.info(
        f"[{channel}] url={url} status={status_code} "
        f"headers={json.dumps(mask_sensitive_data(headers or {}), ensure_ascii=False)} "
        f"payload={json.dumps(mask_sensitive_data(payload or {}), ensure_ascii=False)} "
        f"response={body_preview}"
    )


def _extract_error_message(body: str) -> str:
    try:
        parsed = json.loads(body or "{}")
    except json.JSONDecodeError:
        return ""
    return parsed.get("msg") or parsed.get("message") or ""


def _post_form(url: str, payload: dict, headers: dict, *, channel: str, error_cls, timeout: int = 20):
    encoded = urlencode(payload, doseq=True).encode("utf-8")
    request = Request(url, data=encoded, headers=headers, method="POST")
    try:
        with urlopen(request, timeout=timeout) as response:
            status_code = getattr(response, "status", None)
            body = response.read().decode("utf-8", errors="replace")
            _debug_log(channel, url, payload, headers, status_code=status_code, response_body=body)
    except HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        _debug_log(channel, url, payload, headers, status_code=exc.code, response_body=body)
        raise error_cls(_extract_error_message(body) or f"{channel} HTTP {exc.code}") from exc
    except URLError as exc:
        _debug_log(channel, url, payload, headers, response_body=str(exc))
        raise error_cls("تعذر الوصول إلى الخدمة الخارجية.") from exc
    except TimeoutError as exc:
        _debug_log(channel, url, payload, headers, response_body=str(exc))
        raise error_cls("انتهت مهلة الاتصال بالخدمة الخارجية.") from exc

    try:
        parsed = json.loads(body or "{}")
    except json.JSONDecodeError as exc:
        raise error_cls("استجابة الخدمة الخارجية غير مفهومة.") from exc

    if parsed.get("error") not in (False, 0, None):
        raise error_cls(parsed.get("msg") or parsed.get("message") or "أرجعت الخدمة الخارجية خطأ غير معروف.")
    return parsed


class RadiusApiClient:
    def __init__(self, config: RadiusApiConfig, session_loader=None, session_saver=None):
        self.config = config
        self._session_loader = session_loader
        self._session_saver = session_saver

    @classmethod
    def from_settings(cls, settings: dict | None = None, session_loader=None, session_saver=None):
        settings = settings or {}
        base_url = (os.getenv("RADIUS_API_BASE_URL") or settings.get("base_url") or "").strip().rstrip("/")
        master_api_key = (os.getenv("RADIUS_API_MASTER_KEY") or "").strip()
        username = (os.getenv("RADIUS_API_USERNAME") or settings.get("admin_username") or settings.get("service_username") or "").strip()
        password = (os.getenv("RADIUS_API_PASSWORD") or "").strip()
        api_enabled = bool(settings.get("api_enabled", True))
        return cls(
            RadiusApiConfig(
                base_url=base_url,
                master_api_key=master_api_key,
                username=username,
                password=password,
                api_enabled=api_enabled,
            ),
            session_loader=session_loader,
            session_saver=session_saver,
        )

    def is_configured(self) -> bool:
        return bool(
            self.config.api_enabled
            and self.config.base_url
            and self.config.master_api_key
            and self.config.username
            and self.config.password
        )

    def login(self, force: bool = False) -> str:
        if not self.is_configured():
            raise RadiusApiError("إعدادات تكامل RADIUS غير مكتملة.")

        if not force and self._session_loader:
            cached = self._session_loader()
            if cached and cached.get("api_key"):
                return cached["api_key"]

        payload = self._post(
            self.config.login_url,
            {"username": self.config.username, "password": self.config.password},
            include_master_key=True,
            include_session_key=False,
        )
        account = payload.get("account") or {}
        api_key = account.get("api_key") or payload.get("api_key")
        if not api_key:
            raise RadiusApiError("تعذر الحصول على مفتاح جلسة من خدمة RADIUS.")
        if self._session_saver:
            self._session_saver(api_key)
        return api_key

    def request(self, endpoint: str, data: dict | None = None, include_session_key: bool = True):
        if not self.config.api_enabled:
            raise RadiusApiError("تكامل RADIUS متوقف من الإعدادات.")
        api_key = self.login() if include_session_key else None
        payload = dict(data or {})
        if api_key:
            payload.setdefault("adv_auth_ad", api_key)
        return self._post(
            self.config.endpoint_url(endpoint),
            payload,
            include_master_key=True,
            include_session_key=False,
        )

    def create_user(self, data: dict):
        return self.request("/user_insert", data)

    def update_user(self, data: dict):
        return self.request("/user_update", data)

    def add_time(self, data: dict):
        return self.request("/set_add_time", data)

    def add_quota(self, data: dict, separate: bool = False):
        return self.request("/set_add_qqouta" if separate else "/set_add_qouta", data)

    def set_mac(self, data: dict):
        return self.request("/set_mac", data)

    def reset_password(self, data: dict):
        return self.request("/user_reset_password", data)

    def get_online_users(self, data: dict | None = None):
        return self.request("/get_online_users", data or {})

    def get_user_sessions(self, data: dict):
        return self.request("/get_user_sessions", data)

    def get_user_usage(self, data: dict):
        return self.request("/get_user_usage", data)

    def get_user_bandwidth(self, data: dict):
        return self.request("/get_user_bandwidth", data)

    def get_user_devices(self, data: dict):
        return self.request("/get_user_devices", data)

    def disconnect_user(self, data: dict):
        return self.request("/disconnect_user", data)

    def get_user_cards(self, data: dict):
        return self.request("/get_user_cards", data)

    def generate_user_cards(self, data: dict):
        return self.request("/generate_user_cards", data)

    def validate_card(self, data: dict):
        return self.request("/validate_card", data)

    def get_profile_details(self, data: dict):
        return self.request("/get_profile_details", data)

    def profile_update(self, data: dict):
        return self.request("/profile_update", data)

    def get_profiles_for_user(self, data: dict):
        return self.request("/get_profiles_for_user", data)

    def _post(self, url: str, data: dict, include_master_key: bool = True, include_session_key: bool = False):
        payload = dict(data or {})
        if include_session_key:
            payload.setdefault("adv_auth_ad", self.login())
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        if include_master_key and self.config.master_api_key:
            headers["X-Api-Key"] = self.config.master_api_key
        return _post_form(url, payload, headers, channel="app_ad", error_cls=RadiusApiError)


def default_session_expiry():
    return datetime.now(timezone.utc) + timedelta(hours=8)
