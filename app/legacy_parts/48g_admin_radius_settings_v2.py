# /admin/radius/settings بالتصميم الجديد — override يستخدم القالب الجديد.

from flask import render_template, request, redirect, url_for, flash, session


def _radius_settings_v2_view():
    """إعدادات RADIUS بالـ unified sidebar."""
    settings_row = get_radius_settings_row()
    test_message = ""
    test_category = "info"

    if request.method == "POST":
        action = clean_csv_value(request.form.get("action", "save")) or "save"
        base_url = clean_csv_value(request.form.get("base_url"))
        admin_username = clean_csv_value(request.form.get("admin_username"))
        service_username = clean_csv_value(request.form.get("service_username"))
        api_enabled = request.form.get("api_enabled") == "1"

        execute_sql(
            """
            UPDATE radius_api_settings
            SET base_url=%s, admin_username=%s, service_username=%s, api_enabled=%s,
                updated_at=CURRENT_TIMESTAMP
            WHERE id=%s
            """,
            [base_url, admin_username, service_username, api_enabled, settings_row["id"]],
        )
        try:
            log_action(
                "update_radius_settings",
                "radius_settings",
                settings_row["id"],
                f"base_url={base_url} enabled={api_enabled}",
            )
        except Exception:
            pass
        settings_row = get_radius_settings_row()

        if action == "test":
            try:
                client = get_radius_client()
                client.login(force=True)
                test_message = "تم اختبار الاتصال وتسجيل الدخول الخارجي بنجاح."
                test_category = "success"
            except Exception as exc:
                test_message = f"فشل اختبار الاتصال: {str(exc)}"
                test_category = "error"
        else:
            flash("تم حفظ الإعدادات المحلية. مفاتيح API الحساسة تُقرأ من متغيرات البيئة.", "success")
            return redirect(url_for("radius_settings_page"))

    import os as _os
    env_status = {
        "base": bool(_os.getenv("RADIUS_API_BASE_URL")),
        "master": bool(_os.getenv("RADIUS_API_MASTER_KEY")),
        "user": bool(_os.getenv("RADIUS_API_USERNAME")),
        "password": bool(_os.getenv("RADIUS_API_PASSWORD")),
    }
    env_mode = _os.getenv("RADIUS_MODE", "manual")
    env_ready = _os.getenv("RADIUS_API_READY", "0") in ("1", "true", "True")
    env_writes = _os.getenv("RADIUS_API_WRITES_ENABLED", "0") in ("1", "true", "True")

    return render_template(
        "admin/radius_settings/settings.html",
        settings=settings_row,
        env_status=env_status,
        env_mode=env_mode,
        env_ready=env_ready,
        env_writes=env_writes,
        test_message=test_message,
        test_category=test_category,
    )


# ─── Override /admin/radius/settings القديم ──────────────
_legacy_radius_settings_view = app.view_functions.get("radius_settings_page")


@login_required
@permission_required("manage_radius_settings")
def _new_radius_settings_router():
    """التصميم الجديد افتراضيًا، القديم عبر ?legacy=1"""
    if request.args.get("legacy") == "1" and _legacy_radius_settings_view is not None:
        return _legacy_radius_settings_view()
    return _radius_settings_v2_view()


if "radius_settings_page" in app.view_functions:
    app.view_functions["radius_settings_page"] = _new_radius_settings_router
