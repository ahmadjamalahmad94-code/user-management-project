# 48al_system_cleanup_v2.py
# إعادة تصميم لوحة "تنظيف النظام" بقالب حديث + إمكانيات إضافية:
#   - إحصائيات حية للنظام
#   - تعديل وتنظيف جماعي حسب نوع المشترك (توجيهي/جامعي/عمل حر)
#   - عمليات تصفير شاملة (سجلات/مستفيدين/كل شيء عدا الحسابات)
#   - عمليات صيانة جديدة: إشعارات، طلبات منتهية، بطاقات قديمة، عداد أسبوعي

from flask import render_template, request, redirect, url_for, flash


# ─── إحصائيات سريعة ──────────────────────────────────────────────
def _sys_stats():
    def _c(sql, params=None):
        try:
            row = query_one(sql, params or [])
            return int((row or {}).get("c") or 0)
        except Exception:
            return 0

    return {
        "beneficiaries_total":   _c("SELECT COUNT(*) AS c FROM beneficiaries"),
        "tawjihi":               _c("SELECT COUNT(*) AS c FROM beneficiaries WHERE user_type='tawjihi'"),
        "university":            _c("SELECT COUNT(*) AS c FROM beneficiaries WHERE user_type='university'"),
        "freelancer":            _c("SELECT COUNT(*) AS c FROM beneficiaries WHERE user_type='freelancer'"),
        "portal_accounts":       _c("SELECT COUNT(*) AS c FROM beneficiary_portal_accounts"),
        "usage_logs":            _c("SELECT COUNT(*) AS c FROM beneficiary_usage_logs"),
        "usage_archive":         _c("SELECT COUNT(*) AS c FROM beneficiary_usage_logs_archive"),
        "audit_logs":            _c("SELECT COUNT(*) AS c FROM audit_logs"),
        "issued_cards":          _c("SELECT COUNT(*) AS c FROM beneficiary_issued_cards"),
        "manual_cards":          _c("SELECT COUNT(*) AS c FROM manual_access_cards"),
        "pending_actions":       _c("SELECT COUNT(*) AS c FROM radius_pending_actions WHERE status='pending'"),
        "executed_actions":      _c("SELECT COUNT(*) AS c FROM radius_pending_actions WHERE status IN ('executed','cancelled','rejected','failed','done')"),
        "notifications":         _c("SELECT COUNT(*) AS c FROM notifications"),
        "admin_accounts":        _c("SELECT COUNT(*) AS c FROM app_accounts"),
    }


# ─── الصفحة الرئيسية الجديدة ─────────────────────────────────────
def _system_cleanup_v2_view():
    if not (has_permission('manage_bulk_ops') or has_permission('manage_system_cleanup')):
        flash("غير مصرح لك بهذه الصفحة.", "error")
        return redirect(url_for("dashboard"))

    return render_template(
        "admin/system_cleanup/index.html",
        stats=_sys_stats(),
        TAWJIHI_YEARS=TAWJIHI_YEARS,
        UNIVERSITIES_GAZA=UNIVERSITIES_GAZA,
        INTERNET_ACCESS_METHOD_OPTIONS=INTERNET_ACCESS_METHOD_OPTIONS,
        TIME_MODE_OPTIONS=TIME_MODE_OPTIONS,
        FREELANCER_SCHEDULE_OPTIONS=FREELANCER_SCHEDULE_OPTIONS,
        UNIVERSITY_DAYS_OPTIONS=UNIVERSITY_DAYS_OPTIONS,
    )


# نستبدل الـ view القديم بالحديث (للمسار /admin-control)
if "admin_control_panel" in app.view_functions:
    app.view_functions["admin_control_panel"] = _system_cleanup_v2_view

# نستبدل أيضًا alias المسار /admin/system-cleanup ليعرض الصفحة الجديدة
if "admin_cleanup_alias" in app.view_functions:
    app.view_functions["admin_cleanup_alias"] = _system_cleanup_v2_view

# 48v_force_new_admin_routes أنشأ snapshot قديم — نحدّثه ليشير لـ view الجديد
try:
    if "_CANONICAL_SNAPSHOT" in globals():
        _CANONICAL_SNAPSHOT["admin_control_panel"] = _system_cleanup_v2_view
except Exception:
    pass

# نضمن أن كل URL routes المسجّلة على endpoint admin_control_panel
# (سواء forced أو alias) تستخدم الـ view الجديد
try:
    for _rule in list(app.url_map.iter_rules()):
        if _rule.rule in ("/admin/system-cleanup", "/admin-control"):
            app.view_functions[_rule.endpoint] = _system_cleanup_v2_view
except Exception:
    pass


# ─── عمليات صيانة إضافية (جديدة) ─────────────────────────────────
@app.route("/admin-control/maintenance", methods=["POST"])
@login_required
@permission_required("manage_system_cleanup")
def admin_control_maintenance():
    op = clean_csv_value(request.form.get("operation", ""))
    days = 0
    try:
        days = int(clean_csv_value(request.form.get("days", "30")) or "30")
    except (TypeError, ValueError):
        days = 30
    days = max(1, min(days, 3650))

    msg = ""
    try:
        if op == "clear_notifications":
            execute_sql("DELETE FROM notifications")
            msg = "تم حذف كل الإشعارات."
        elif op == "clear_old_notifications":
            execute_sql(
                "DELETE FROM notifications WHERE created_at < datetime('now', %s)"
                if is_sqlite_database_url()
                else "DELETE FROM notifications WHERE created_at < NOW() - (%s || ' days')::interval",
                [f"-{days} days"] if is_sqlite_database_url() else [str(days)],
            )
            msg = f"تم حذف الإشعارات الأقدم من {days} يوم."
        elif op == "clear_executed_actions":
            execute_sql(
                "DELETE FROM radius_pending_actions WHERE status IN ('executed','cancelled','rejected','failed','done')"
            )
            msg = "تم حذف الطلبات المنجزة والمرفوضة."
        elif op == "clear_old_executed_actions":
            execute_sql(
                "DELETE FROM radius_pending_actions WHERE status IN ('executed','cancelled','rejected','failed','done') AND requested_at < datetime('now', %s)"
                if is_sqlite_database_url()
                else "DELETE FROM radius_pending_actions WHERE status IN ('executed','cancelled','rejected','failed','done') AND requested_at < NOW() - (%s || ' days')::interval",
                [f"-{days} days"] if is_sqlite_database_url() else [str(days)],
            )
            msg = f"تم حذف الطلبات المنجزة الأقدم من {days} يوم."
        elif op == "clear_issued_cards":
            execute_sql("DELETE FROM beneficiary_issued_cards")
            msg = "تم حذف سجل البطاقات المُصدَرة بالكامل."
        elif op == "clear_old_issued_cards":
            execute_sql(
                "DELETE FROM beneficiary_issued_cards WHERE issued_at < datetime('now', %s)"
                if is_sqlite_database_url()
                else "DELETE FROM beneficiary_issued_cards WHERE issued_at < NOW() - (%s || ' days')::interval",
                [f"-{days} days"] if is_sqlite_database_url() else [str(days)],
            )
            msg = f"تم حذف البطاقات الصادرة الأقدم من {days} يوم."
        elif op == "clear_manual_inventory":
            # نحذف فقط البطاقات اللي لم تُصرف
            execute_sql(
                """
                DELETE FROM manual_access_cards
                WHERE NOT EXISTS (
                    SELECT 1 FROM beneficiary_issued_cards bic
                    WHERE bic.card_username = manual_access_cards.card_username
                      AND bic.card_password = manual_access_cards.card_password
                )
                """
            )
            msg = "تم حذف كل البطاقات المتاحة في المخزون (الصادرة محفوظة)."
        elif op == "reset_all_weekly_usage":
            execute_sql(
                "UPDATE beneficiaries SET weekly_usage_count=0, weekly_usage_week_start=%s",
                [get_week_start()],
            )
            msg = "تم تصفير عدّاد الاستخدام الأسبوعي لكل المستفيدين."
        elif op == "clear_old_audit":
            execute_sql(
                "DELETE FROM audit_logs WHERE created_at < datetime('now', %s)"
                if is_sqlite_database_url()
                else "DELETE FROM audit_logs WHERE created_at < NOW() - (%s || ' days')::interval",
                [f"-{days} days"] if is_sqlite_database_url() else [str(days)],
            )
            msg = f"تم حذف سجلات التدقيق الأقدم من {days} يوم."
        elif op == "clear_archive":
            execute_sql("DELETE FROM beneficiary_usage_logs_archive")
            msg = "تم حذف أرشيف الاستخدام بالكامل."
        elif op == "clear_audit_logs":
            execute_sql("DELETE FROM audit_logs")
            msg = "تم حذف سجل التدقيق بالكامل."
        else:
            flash("عملية صيانة غير معروفة.", "error")
            return redirect(url_for("admin_control_panel"))

        log_action("maintenance", "system", None, f"op={op} days={days}")
        flash(msg, "success")
    except Exception as e:
        flash(f"تعذّر تنفيذ العملية: {e}", "error")

    return redirect(url_for("admin_control_panel"))
