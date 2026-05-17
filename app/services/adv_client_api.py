from __future__ import annotations

import os
from dataclasses import dataclass

import requests

from .radius_api import _debug_log, _extract_error_message, mask_sensitive_data


class AdvClientApiError(Exception):
    pass


@dataclass
class AdvClientApiConfig:
    base_url: str
    username: str
    password: str
    api_enabled: bool = True

    @property
    def login_url(self) -> str:
        return f"{self.base_url.rstrip('/')}/login"

    def endpoint_url(self, endpoint: str) -> str:
        return f"{self.base_url.rstrip('/')}/{endpoint.lstrip('/')}"


class AdvClientApi:
    def __init__(self, config: AdvClientApiConfig, session_loader=None, session_saver=None):
        self.config = config
        self._session_loader = session_loader
        self._session_saver = session_saver
        self._session = requests.Session()

    @classmethod
    def from_env(cls, session_loader=None, session_saver=None):
        base_url = (
            os.getenv("ADV_APP_API_BASE_URL")
            or os.getenv("ADVRADIUS_APP_BASE_URL")
            or "http://advrapp.com:6950/app"
        ).strip().rstrip("/")
        username = (os.getenv("ADV_APP_DEFAULT_USERNAME") or os.getenv("ADVRADIUS_APP_USERNAME") or "").strip()
        password = (os.getenv("ADV_APP_DEFAULT_PASSWORD") or os.getenv("ADVRADIUS_APP_PASSWORD") or "").strip()
        api_enabled = (
            os.getenv("ADV_APP_API_ENABLED")
            or os.getenv("ADVRADIUS_APP_ENABLED")
            or "1"
        ).strip().lower() not in {"0", "false", "no", "off"}
        return cls(
            AdvClientApiConfig(
                base_url=base_url,
                username=username,
                password=password,
                api_enabled=api_enabled,
            ),
            session_loader=session_loader,
            session_saver=session_saver,
        )

    def is_configured(self) -> bool:
        return bool(self.config.api_enabled and self.config.base_url and self.config.username and self.config.password)

    def login(self, username: str | None = None, password: str | None = None, force: bool = False) -> dict:
        login_username = (username or self.config.username or "").strip()
        login_password = (password or self.config.password or "").strip()
        if not self.config.api_enabled:
            raise AdvClientApiError("تكامل AdvRadius Client API متوقف من الإعدادات.")
        if not login_username or not login_password or not self.config.base_url:
            raise AdvClientApiError("إعدادات AdvRadius Client API غير مكتملة.")

        if not force and username is None and password is None and self._session_loader:
            cached = self._session_loader()
            if cached and cached.get("api_key"):
                return cached

        payload = self._post(
            self.config.login_url,
            {"username": login_username, "password": login_password},
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            channel="adv_client_app",
        )
        account = payload.get("account") or {}
        api_key = account.get("api_key")
        if not api_key:
            raise AdvClientApiError("تعذر استخراج account.api_key من استجابة تسجيل الدخول.")
        session_data = {"api_key": api_key, "account": account}
        if username is None and password is None and self._session_saver:
            self._session_saver(session_data)
        return session_data

    def request(self, endpoint: str, api_key: str | None = None, data: dict | None = None, force_login: bool = False):
        if not self.config.api_enabled:
            raise AdvClientApiError("تكامل AdvRadius Client API متوقف من الإعدادات.")
        active_api_key = (api_key or "").strip()
        if not active_api_key:
            active_api_key = self.login(force=force_login).get("api_key", "")
        if not active_api_key:
            raise AdvClientApiError("تعذر الحصول على adv_auth.")
        return self._post(
            self.config.endpoint_url(endpoint),
            dict(data or {}),
            headers={
                "Content-Type": "application/x-www-form-urlencoded",
                "adv_auth": active_api_key,
            },
            channel="adv_client_app",
        )

    def details(self, api_key: str | None = None):
        return self.request("/details", api_key=api_key, data={})

    def status(self, api_key: str | None = None):
        return self.request("/status", api_key=api_key, data={})

    def profiles(self, api_key: str | None = None):
        return self.request("/profiles", api_key=api_key, data={})

    def get_profiles(self, api_key: str | None = None):
        return self.request("/getprofiles", api_key=api_key, data={})

    def set_profile(self, api_key: str | None = None, profile_id: str | int | None = None):
        return self.request("/setprofile", api_key=api_key, data={"profile_id": profile_id or ""})

    def band(self, api_key: str | None = None):
        return self.request("/band", api_key=api_key, data={})

    def logout(self, api_key: str | None = None):
        return self.request("/logout", api_key=api_key, data={})

    def _post(self, url: str, data: dict, headers: dict, channel: str):
        try:
            response = self._session.post(url, data=data, headers=headers, timeout=20)
            _debug_log(channel, url, data, headers, status_code=response.status_code, response_body=response.text)
        except requests.Timeout as exc:
            _debug_log(channel, url, data, headers, response_body=str(exc))
            raise AdvClientApiError("انتهت مهلة الاتصال بخدمة AdvRadius Client API.") from exc
        except requests.RequestException as exc:
            _debug_log(channel, url, data, headers, response_body=str(exc))
            raise AdvClientApiError("تعذر الوصول إلى خدمة AdvRadius Client API.") from exc

        if response.status_code >= 400:
            raise AdvClientApiError(_extract_error_message(response.text) or f"{channel} HTTP {response.status_code}")

        try:
            parsed = response.json()
        except ValueError as exc:
            raise AdvClientApiError("استجابة AdvRadius Client API غير مفهومة.") from exc

        if parsed.get("error") not in (False, 0, None):
            raise AdvClientApiError(parsed.get("msg") or parsed.get("message") or "أرجعت AdvRadius Client API خطأ غير معروف.")
        return parsed


def summarize_adv_client_test(result: dict) -> dict:
    return {
        "account": mask_sensitive_data(result.get("account") or {}),
        "details": mask_sensitive_data(result.get("details") or {}),
    }
