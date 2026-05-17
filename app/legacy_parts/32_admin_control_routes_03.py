# Continued split from 32_admin_control_routes.py lines 256-352. Loaded by app.legacy.

@app.route("/admin-control/apply-update", methods=["POST"])
@login_required
@permission_required("manage_bulk_ops")
def admin_control_apply_update():
    filters = admin_scope_values(request.form)
    operation = clean_csv_value(request.form.get("operation", ""))
    new_value = clean_csv_value(request.form.get("new_value", ""))
    if not operation:
        flash("اختر نوع التعديل أولًا.", "error")
        return redirect(url_for("admin_control_panel"))
    mapping = {
        "set_university_internet_method": ("university_internet_method = %s", [new_value]),
        "set_university_time_mode": ("university_time_mode = %s", [new_value]),
        "set_university_days": ("university_days = %s", [new_value]),
        "set_university_time_from": ("university_time_from = %s", [new_value]),
        "set_university_time_to": ("university_time_to = %s", [new_value]),
        "set_freelancer_internet_method": ("freelancer_internet_method = %s", [new_value]),
        "set_freelancer_time_mode": ("freelancer_time_mode = %s", [new_value]),
        "set_freelancer_schedule_type": ("freelancer_schedule_type = %s", [new_value]),
        "set_freelancer_time_from": ("freelancer_time_from = %s", [new_value]),
        "set_freelancer_time_to": ("freelancer_time_to = %s", [new_value]),
        "set_notes": ("notes = %s", [new_value]),
    }
    if operation not in mapping:
        flash("عملية التعديل غير مدعومة.", "error")
        return redirect(url_for("admin_control_panel"))
    affected = count_admin_targets(filters)
    if affected == 0:
        flash("لا يوجد مستفيدون مطابقون لهذا القسم/الفلتر.", "error")
        return redirect(url_for("admin_control_panel"))
    set_sql, values = mapping[operation]
    execute_admin_update(filters, set_sql, values)
    summary = admin_target_summary(filters)
    log_action("edit", "beneficiary", None, f"Admin control update | op={operation} | target={summary} | affected={affected}")
    flash(f"تم تنفيذ التعديل على {affected} مستفيد ({summary}).", "success")
    return redirect(url_for("admin_control_panel"))

@app.route("/admin-control/apply-clean", methods=["POST"])
@login_required
@permission_required("manage_system_cleanup")
def admin_control_apply_clean():
    filters = admin_scope_values(request.form)
    operation = clean_csv_value(request.form.get("operation", ""))
    if not operation:
        flash("اختر نوع التنظيف أولًا.", "error")
        return redirect(url_for("admin_control_panel"))
    mapping = {
        "clear_notes": ("notes = ''", []),
        "clear_phones": ("phone = ''", []),
        "reset_weekly_usage": ("weekly_usage_count = 0, weekly_usage_week_start = %s", [get_week_start()]),
        "clear_times": ("freelancer_time_from = '', freelancer_time_to = '', university_time_from = '', university_time_to = ''", []),
        "clear_internet_methods": ("freelancer_internet_method = '', university_internet_method = ''", []),
        "clear_days": ("university_days = ''", []),
        "clear_schedule": ("freelancer_schedule_type = ''", []),
    }
    if operation not in mapping:
        flash("عملية التنظيف غير مدعومة.", "error")
        return redirect(url_for("admin_control_panel"))
    affected = count_admin_targets(filters)
    if affected == 0:
        flash("لا يوجد مستفيدون مطابقون لهذا القسم/الفلتر.", "error")
        return redirect(url_for("admin_control_panel"))
    set_sql, values = mapping[operation]
    execute_admin_update(filters, set_sql, values)
    summary = admin_target_summary(filters)
    log_action("edit", "beneficiary", None, f"Admin control clean | op={operation} | target={summary} | affected={affected}")
    flash(f"تم تنفيذ التنظيف على {affected} مستفيد ({summary}).", "success")
    return redirect(url_for("admin_control_panel"))

@app.route("/admin-control/system-reset", methods=["POST"])
@login_required
@permission_required("manage_system_cleanup")
def admin_control_system_reset():
    operation = clean_csv_value(request.form.get("operation", ""))
    if operation == "truncate_operational":
        execute_admin_sql("TRUNCATE TABLE beneficiary_usage_logs RESTART IDENTITY CASCADE")
        execute_admin_sql("TRUNCATE TABLE beneficiary_usage_logs_archive RESTART IDENTITY CASCADE")
        execute_admin_sql("TRUNCATE TABLE audit_logs RESTART IDENTITY")
        message = "تم تنظيف السجلات التشغيلية بنجاح."
    elif operation == "truncate_beneficiaries_only":
        execute_admin_sql("TRUNCATE TABLE beneficiary_usage_logs RESTART IDENTITY CASCADE")
        execute_admin_sql("TRUNCATE TABLE beneficiary_usage_logs_archive RESTART IDENTITY CASCADE")
        execute_admin_sql("TRUNCATE TABLE beneficiaries RESTART IDENTITY CASCADE")
        message = "تم حذف كل المستفيدين والسجلات المرتبطة بهم."
    elif operation == "truncate_everything_except_accounts":
        execute_admin_sql("TRUNCATE TABLE beneficiary_usage_logs RESTART IDENTITY CASCADE")
        execute_admin_sql("TRUNCATE TABLE beneficiary_usage_logs_archive RESTART IDENTITY CASCADE")
        execute_admin_sql("TRUNCATE TABLE beneficiaries RESTART IDENTITY CASCADE")
        execute_admin_sql("TRUNCATE TABLE audit_logs RESTART IDENTITY")
        message = "تم تصفير كل بيانات التشغيل مع الإبقاء على الحسابات والصلاحيات."
    else:
        flash("عملية التصفير غير معروفة.", "error")
        return redirect(url_for("admin_control_panel"))
    log_action("backup", "beneficiary", None, f"Admin system reset | op={operation}")
    flash(message, "success")
    return redirect(url_for("admin_control_panel"))
