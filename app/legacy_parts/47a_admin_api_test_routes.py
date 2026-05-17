# صفحة اختبار اتصال RADIUS API — قراءة فقط.

import json as _json
import os
from flask import flash, redirect, render_template, request, session, url_for
from app.utils.arabic_terms import arabize_text


def _mask(value: str, show: int = 4) -> str:
    if not value:
        return ""
    if len(value) <= show:
        return "*" * len(value)
    return value[:show] + "•" * (len(value) - show)


def _env_status():
    """يجمع حالة متغيرات البيئة المتعلقة بـ RADIUS."""
    keys = [
        ("RADIUS_API_BASE_URL", "رابط واجهة المصادقة"),
        ("RADIUS_API_MASTER_KEY", "المفتاح الرئيسي"),
        ("RADIUS_API_USERNAME", "حساب الربط"),
        ("RADIUS_API_PASSWORD", "كلمة مرور الربط"),
        ("RADIUS_MODE", "وضع التشغيل"),
        ("RADIUS_API_READY", "جاهزية الربط"),
        ("RADIUS_API_WRITES_ENABLED", "صلاحية الكتابة"),
    ]
    out = {}
    for k, label in keys:
        v = os.getenv(k, "")
        if k in ("RADIUS_API_MASTER_KEY", "RADIUS_API_PASSWORD"):
            display = "مضبوط ومخفي" if v else ""
        elif k == "RADIUS_MODE":
            display = arabize_text(v) if v else ""
        elif k == "RADIUS_API_READY":
            display = "جاهز" if v in {"1", "true", "True", "yes", "on"} else ("غير جاهز" if v else "")
        elif k == "RADIUS_API_WRITES_ENABLED":
            display = "مفعلة" if v in {"1", "true", "True", "yes", "on"} else ("معطلة" if v else "")
        else:
            display = "مضبوط" if v else ""
        out[k] = {"label": label, "set": bool(v), "value": display}
    return out


@app.route("/admin/api/test", methods=["GET"])
@admin_login_required
def admin_api_test():
    from app.services.radius_client import is_api_under_development
    api_ready = not is_api_under_development()
    return render_template(
        "admin/api/connection_test.html",
        env_status=_env_status(),
        api_ready=api_ready,
        last_test=session.pop("api_last_test", None),
        last_result=session.pop("api_last_result", None),
        last_ok=session.pop("api_last_ok", False),
    )


@app.route("/admin/api/test/run", methods=["POST"], endpoint="admin_api_test_run")
@admin_login_required
def admin_api_test_run_handler():
    from app.services.radius_client import get_radius_client, is_live_mode, is_api_under_development

    test = clean_csv_value(request.form.get("test")) or "health_check"

    if not is_live_mode():
        flash("وضع خدمة المصادقة ليس مباشرًا. فعّل الوضع المباشر من إعدادات التشغيل ثم أعد التشغيل.", "error")
        return redirect(url_for("admin_api_test"))

    if is_api_under_development():
        flash("واجهة الربط غير مفعّلة. فعّل جاهزية الربط من إعدادات التشغيل.", "error")
        return redirect(url_for("admin_api_test"))

    client = get_radius_client()
    results = []
    overall_ok = True

    def _run(name, fn):
        nonlocal overall_ok
        try:
            r = fn()
            ok = bool(r.get("ok"))
            overall_ok = overall_ok and ok
            results.append({
                "name": name,
                "ok": ok,
                "data": r,
            })
        except Exception as exc:
            overall_ok = False
            results.append({
                "name": name,
                "ok": False,
                "data": {"error": str(exc)},
            })

    if test == "health_check":
        _run("فحص الاتصال", client.health_check)
    elif test == "permissions":
        _run("قراءة صلاحياتي", client.get_my_permissions)
    elif test == "balance":
        _run("قراءة رصيدي", client.get_my_balance)
    elif test == "server_status":
        _run("قراءة حالة الخادم", client.get_server_status)
    elif test == "online_users":
        def _online_wrap():
            sessions = client.get_online_users()
            return {"ok": True, "count": len(sessions), "sessions": sessions[:20]}
        _run("قراءة المتصلين الآن", _online_wrap)
    elif test == "quick_stats":
        _run("إحصائيات سريعة", client.quick_stats)
    elif test == "dashboard_metrics":
        _run("قراءة مؤشرات اللوحة", client.get_dashboard_metrics)
    elif test == "profiles":
        def _profiles_wrap():
            ps = client.get_profiles()
            return {"ok": True, "count": len(ps), "profiles": ps[:20]}
        _run("قراءة الباقات", _profiles_wrap)
    elif test == "search_demo":
        _run("تجربة بحث المشتركين", lambda: client.search_users("", limit=10))
    elif test == "full_suite":
        _run("1) فحص الاتصال", client.health_check)
        _run("2) قراءة صلاحياتي", client.get_my_permissions)
        _run("3) قراءة رصيدي", client.get_my_balance)
        _run("4) قراءة حالة الخادم", client.get_server_status)
        _run("5) إحصائيات سريعة", client.quick_stats)
        _run("6) قراءة المتصلين الآن", lambda: {"ok": True, "count": len(client.get_online_users())})
        _run("7) قراءة الباقات", lambda: {"ok": True, "count": len(client.get_profiles())})
    else:
        flash("اختبار غير معروف.", "error")
        return redirect(url_for("admin_api_test"))

    # نبني تقرير نصي للعرض
    lines = []
    for r in results:
        icon = "✅" if r["ok"] else "❌"
        lines.append(f"{icon} {r['name']}")
        try:
            pretty = _json.dumps(r["data"], ensure_ascii=False, indent=2)
        except Exception:
            pretty = str(r["data"])
        pretty = arabize_text(pretty)
        # اقتطاع لو طويل
        if len(pretty) > 2000:
            pretty = pretty[:2000] + "\n... (مقتطع)"
        lines.append(pretty)
        lines.append("─" * 60)

    session["api_last_test"] = test
    session["api_last_result"] = "\n".join(lines)
    session["api_last_ok"] = overall_ok

    log_action(
        "api_test_run",
        "radius_api",
        0,
        f"اختبار الربط={arabize_text(test)} النتيجة={'ناجح' if overall_ok else 'فشل'}",
    )

    return redirect(url_for("admin_api_test"))



@app.route("/admin/api/test/reset", methods=["POST"], endpoint="admin_api_test_reset")
@admin_login_required
def admin_api_test_reset_handler():
    """يعيد تعيين الـ RadiusClient singleton — يمسح أي fail cache أو api_key محفوظ."""
    from app.services.radius_client import reset_radius_client
    reset_radius_client()
    log_action("api_test_reset", "radius_api", 0, "إعادة تعيين عميل واجهة المصادقة يدويًا")
    flash("تمت إعادة تعيين عميل الربط. حاول الاختبار من جديد.", "success")
    return redirect(url_for("admin_api_test"))
