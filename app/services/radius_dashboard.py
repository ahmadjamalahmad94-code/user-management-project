"""
radius_dashboard — طبقة عرض الـ API على الـ Dashboards.

تجلب البيانات من LiveRadiusClient مع cache بسيط لـ 30 ثانية لتجنّب
استدعاءات متكررة عند تحديث صفحات الإدارة.

الاستخدام:
    from app.services.radius_dashboard import get_radius_kpis

    kpis = get_radius_kpis()  # dict بفlags + قيم
    if kpis['available']:
        print(kpis['data']['online_users'])
    else:
        print(kpis['error'])

كل دالة ترجع:
    {
      "available": bool,           # هل الـ API ردّ بنجاح؟
      "data": dict | list | None,  # البيانات إن نجح
      "error": str,                # رسالة خطأ إن فشل
      "cached": bool,              # هل النتيجة من الكاش؟
      "age_seconds": int,          # عمر الكاش
    }
"""
from __future__ import annotations

import time
from typing import Any, Callable

from .radius_client import get_radius_client, is_api_under_development
from .radius_kill_switch import is_radius_offline, OFFLINE_REASON


# ─── كاش بسيط ──────────────────────────────────────────────────────
_CACHE: dict[str, tuple[float, Any]] = {}
_CACHE_TTL = 30  # ثوانٍ


def _cached(key: str, fetch_fn: Callable[[], Any]) -> dict:
    """ينفذ fetch_fn إن انتهت صلاحية الكاش، ويرجع نتيجة موحّدة."""
    now = time.time()
    cached = _CACHE.get(key)

    if cached:
        ts, payload = cached
        age = now - ts
        if age < _CACHE_TTL:
            return {**payload, "cached": True, "age_seconds": int(age)}

    # ⚡ Kill-switch موحّد: لا أي استدعاء HTTP إذا كان API معطّل
    if is_radius_offline() or is_api_under_development():
        result = {
            "available": False,
            "data": None,
            "error": OFFLINE_REASON,
            "cached": False,
            "age_seconds": 0,
        }
        _CACHE[key] = (now, result)
        return result

    try:
        data = fetch_fn()
        result = {
            "available": True,
            "data": data,
            "error": "",
            "cached": False,
            "age_seconds": 0,
        }
    except Exception as exc:
        result = {
            "available": False,
            "data": None,
            "error": str(exc),
            "cached": False,
            "age_seconds": 0,
        }
    _CACHE[key] = (now, result)
    return result


def invalidate_cache(key: str | None = None):
    """مسح الكاش يدويًا."""
    if key is None:
        _CACHE.clear()
    else:
        _CACHE.pop(key, None)


# ─── الواجهات للاستخدام في الـ routes ──────────────────────────────
def get_radius_kpis() -> dict:
    """quick_stats للداشبورد الإداري."""
    def _fetch():
        c = get_radius_client()
        r = c.quick_stats()
        if not r.get("ok"):
            raise RuntimeError(r.get("error") or "quick_stats failed")
        return r.get("data") or {}
    return _cached("radius:quick_stats", _fetch)


def get_radius_online_users(limit: int = 50) -> dict:
    """قائمة الجلسات النشطة."""
    def _fetch():
        c = get_radius_client()
        sessions = c.get_online_users() or []
        return sessions[:limit]
    return _cached("radius:online_users", _fetch)


def get_radius_profiles() -> dict:
    """قائمة الباقات في RADIUS."""
    def _fetch():
        c = get_radius_client()
        return c.get_profiles() or []
    return _cached("radius:profiles", _fetch)


def get_radius_balance() -> dict:
    """رصيد المدير الحالي."""
    def _fetch():
        c = get_radius_client()
        r = c.get_my_balance()
        if not r.get("ok"):
            raise RuntimeError(r.get("error") or "balance failed")
        return r.get("data") or {}
    return _cached("radius:balance", _fetch)


def get_radius_server_info() -> dict:
    """معلومات السيرفر (للحالة في footer)."""
    def _fetch():
        c = get_radius_client()
        r = c.health_check()
        if not r.get("ok"):
            raise RuntimeError(r.get("error") or "health_check failed")
        return r.get("data") or {}
    return _cached("radius:server_info", _fetch)
