from __future__ import annotations

import os
from dataclasses import dataclass
from urllib.parse import urlencode

from app.config import MIKROTIK_HOTSPOT_URL


@dataclass(frozen=True)
class HotspotConnectUrls:
    logout_url: str
    login_url: str


def hotspot_base_url() -> str:
    return (os.getenv("MIKROTIK_HOTSPOT_URL") or MIKROTIK_HOTSPOT_URL or "").strip().rstrip("/")


def hotspot_url(path: str, params: dict[str, str] | None = None) -> str:
    base_url = hotspot_base_url()
    if not base_url:
        raise ValueError("MIKROTIK_HOTSPOT_URL is not configured.")

    url = f"{base_url}/{path.lstrip('/')}"
    if params:
        url = f"{url}?{urlencode(params)}"
    return url


def hotspot_login_url() -> str:
    base_url = hotspot_base_url()
    return f"{base_url}/login" if base_url else ""


def build_card_connect_urls(*, card_username: str, card_password: str) -> HotspotConnectUrls:
    return HotspotConnectUrls(
        logout_url=hotspot_url("logout"),
        login_url=hotspot_url(
            "login",
            {
                "username": card_username or "",
                "password": card_password or "",
            },
        ),
    )
