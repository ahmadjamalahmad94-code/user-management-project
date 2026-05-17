"""
radius_subscriber_bridge — جسر بين بيانات HobeHub والـ Admin API.
يستخدم admin master key لجلب/تعديل بيانات مشترك معيّن نيابة عنه.

⚠ كل دالة استدعاء API هنا محكومة بـ kill-switch موحّد:
   - افتراضياً معطّلة (لا تستدعي شبكة).
   - للتفعيل: RADIUS_API_LIVE=1 في البيئة.
"""
from __future__ import annotations

from typing import Any
from app.services.radius_api import RadiusApiClient, RadiusApiError
from app.services.adv_client_api import AdvClientApi, AdvClientApiError
from app.services.radius_kill_switch import is_radius_offline, radius_offline_response


# ───────── Username lookup ─────────
def get_radius_username_for(beneficiary_row: dict) -> str:
    """يرجّع اسم المستخدم في RADIUS لمشترك معيّن.
       يجرّب أولاً radius_username ثم phone."""
    if not beneficiary_row:
        return ""
    for key in ("radius_username", "username", "phone"):
        v = (beneficiary_row.get(key) or "").strip()
        if v:
            return v
    return ""


# ───────── Admin API client (cached + session reused) ─────────
_admin_client: RadiusApiClient | None = None
_session_cache: dict = {"api_key": None, "ts": 0}


def _load_session():
    """يرجع الـ api_key المحفوظ في الذاكرة (لمنع تكرار login يستهلك rate-limit)."""
    if _session_cache.get("api_key"):
        return {"api_key": _session_cache["api_key"]}
    return None


def _save_session(api_key):
    """يخزّن الـ api_key في الذاكرة."""
    import time as _t
    _session_cache["api_key"] = api_key
    _session_cache["ts"] = _t.time()


def _clear_session():
    _session_cache["api_key"] = None
    _session_cache["ts"] = 0


def _get_admin_client() -> RadiusApiClient:
    global _admin_client
    if _admin_client is None:
        _admin_client = RadiusApiClient.from_settings(
            session_loader=_load_session,
            session_saver=_save_session,
        )
    return _admin_client


# ───────── Status: details + status combined ─────────
def fetch_subscriber_status(username: str) -> dict:
    """يجلب details + status لمشترك. يرجع dict موحّد أو {'ok':False, 'error':...}."""
    if is_radius_offline():
        return radius_offline_response({"username": username})
    if not username:
        return {"ok": False, "error": "اسم المستخدم غير محدد."}
    try:
        client = _get_admin_client()
        if not client.is_configured():
            return {"ok": False, "error": "إعدادات RADIUS API غير مكتملة."}
        # نستخدم get_user_usage للحصول على ملخّص الاستهلاك
        usage = client.get_user_usage({"username": username})
        sessions = {}
        try:
            sessions = client.get_user_sessions({"username": username})
        except Exception:
            pass
        return {
            "ok": True,
            "username": username,
            "usage": usage or {},
            "sessions": sessions or {},
        }
    except RadiusApiError as e:
        return {"ok": False, "error": str(e)}
    except Exception as e:
        return {"ok": False, "error": f"{type(e).__name__}: {e}"}


# ───────── Password reset (via admin API) ─────────
def reset_subscriber_password(username: str, new_password: str) -> dict:
    if is_radius_offline():
        return radius_offline_response({"username": username})
    if not username or not new_password:
        return {"ok": False, "error": "اسم المستخدم وكلمة المرور مطلوبان."}
    if len(new_password) < 6:
        return {"ok": False, "error": "كلمة المرور قصيرة جدًا (6 أحرف على الأقل)."}
    try:
        client = _get_admin_client()
        if not client.is_configured():
            return {"ok": False, "error": "إعدادات RADIUS API غير مكتملة."}
        result = client.reset_password({
            "username": username,
            "password": new_password,
            "new_password": new_password,
        })
        return {"ok": True, "result": result or {}}
    except RadiusApiError as e:
        return {"ok": False, "error": str(e)}
    except Exception as e:
        return {"ok": False, "error": f"{type(e).__name__}: {e}"}


# ───────── Online users (for live monitor) ─────────
def fetch_online_users(limit: int = 100) -> dict:
    if is_radius_offline():
        return radius_offline_response({"data": {}})
    try:
        client = _get_admin_client()
        if not client.is_configured():
            return {"ok": False, "error": "إعدادات RADIUS API غير مكتملة."}
        result = client.get_online_users({"limit": limit})
        return {"ok": True, "data": result or {}}
    except RadiusApiError as e:
        return {"ok": False, "error": str(e)}
    except Exception as e:
        return {"ok": False, "error": f"{type(e).__name__}: {e}"}


# ───────── Subscriber API (when we have their creds) ─────────
def fetch_subscriber_details_via_self(username: str, password: str) -> dict:
    """يجلب /details + /status باستخدام كريدنشيال المشترك نفسه (الـ AdvClient API)."""
    if is_radius_offline():
        return radius_offline_response({"username": username})
    if not username or not password:
        return {"ok": False, "error": "اسم المستخدم وكلمة المرور مطلوبان."}
    client = AdvClientApi.from_env()
    if not (client.config.api_enabled and client.config.base_url):
        return {"ok": False, "error": "AdvRadius Client API غير مهيّأ."}
    try:
        login_data = client.login(username=username, password=password, force=True)
        api_key = login_data.get("api_key")
        if not api_key:
            return {"ok": False, "error": "فشل تسجيل دخول المشترك."}
        details = client.request("/details", api_key=api_key, data={})
        status_d = {}
        try:
            status_d = client.request("/status", api_key=api_key, data={})
        except Exception:
            pass
        return {
            "ok": True,
            "username": username,
            "details": details or {},
            "status": status_d or {},
            "account": login_data.get("account") or {},
        }
    except AdvClientApiError as e:
        return {"ok": False, "error": str(e)}
    except Exception as e:
        return {"ok": False, "error": f"{type(e).__name__}: {e}"}
