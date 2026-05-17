"""
RadiusClient — طبقة عزل بين باقي التطبيق وخدمة RADIUS الخارجية.

استخدام:
    from app.services.radius_client import get_radius_client

    client = get_radius_client()
    result = client.generate_user_cards(category_code="one_hour", count=1)

الاختيار بين النسخة اليدوية (ManualRadiusClient) والنسخة الحية (LiveRadiusClient)
يتم عبر متغير البيئة RADIUS_MODE.

القيم المدعومة:
    - "manual" (الافتراضي): يكتب العمليات في جدول radius_pending_actions ولا يتصل بأي API.
    - "live"  : يستدعي app_ad API الفعلي. ⚠️ معطّل في Phase 1.

⚠️ تنبيه Phase 1: حتى لو RADIUS_MODE=live، نمنع الاتصال الفعلي تلقائيًا.
سنفعّل الـ live بعد الاختبار الكامل والتحقق من الـ API.
"""
from __future__ import annotations

import os

from .base import RadiusClient, RadiusClientError, RadiusClientNotImplemented
from .dtos import (
    Card,
    PendingAction,
    Profile,
    Session,
    UsageSnapshot,
    UserAccount,
)
from .manual import ManualRadiusClient
from .live import LiveRadiusClient


__all__ = [
    "RadiusClient",
    "RadiusClientError",
    "RadiusClientNotImplemented",
    "Card",
    "PendingAction",
    "Profile",
    "Session",
    "UsageSnapshot",
    "UserAccount",
    "get_radius_client",
    "is_live_mode",
    "is_api_under_development",
]


def get_radius_mode() -> str:
    """يرجع الـ mode الحالي من البيئة. الافتراضي: 'manual'."""
    return (os.getenv("RADIUS_MODE", "manual") or "manual").strip().lower()


def is_live_mode() -> bool:
    return get_radius_mode() == "live"


def is_api_under_development() -> bool:
    """
    قيد التطوير = الـ API لم يُختبر بعد.
    حاليًا دائمًا True بغض النظر عن RADIUS_MODE.
    عند الانتقال لـ Phase 2، نضبط RADIUS_API_READY=1 في البيئة.
    """
    if not is_live_mode():
        return True
    return os.getenv("RADIUS_API_READY", "").strip().lower() not in {"1", "true", "yes", "on"}


_singleton: RadiusClient | None = None


def get_radius_client() -> RadiusClient:
    """
    factory رئيسي. يحدّد النسخة المناسبة من البيئة، ويُرجع نسخة وحيدة (singleton).
    """
    global _singleton
    if _singleton is not None:
        return _singleton

    if is_live_mode() and not is_api_under_development():
        _singleton = LiveRadiusClient()
    else:
        # الافتراضي + أي وضع غير جاهز = manual آمن
        _singleton = ManualRadiusClient()
    return _singleton


def reset_radius_client() -> None:
    """يستخدم في الاختبارات لإعادة الـ singleton."""
    global _singleton
    _singleton = None
