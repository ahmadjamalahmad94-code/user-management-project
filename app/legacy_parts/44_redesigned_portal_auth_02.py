# Continued split from 44_redesigned_portal_auth.py lines 118-173. Loaded by app.legacy.


def _redesigned_user_login():
    if session.get("portal_type") == "beneficiary" and session.get("beneficiary_id"):
        return redirect(url_for("user_dashboard"))
    if session.get("portal_type") == "admin" and session.get("account_id"):
        return redirect(url_for("dashboard"))
    if request.method == "POST":
        username = normalize_portal_username(request.form.get("username"))
        password = clean_csv_value(request.form.get("password"))
        row = get_beneficiary_portal_account_by_username(username)
        if not row:
            flash("بيانات الدخول غير صحيحة.", "error")
            return redirect(url_for("user_login"))
        if portal_account_is_locked(row):
            flash("تم إيقاف المحاولة مؤقتًا. يرجى المحاولة لاحقًا.", "error")
            return redirect(url_for("user_login"))
        if row.get("must_set_password"):
            flash("الحساب يحتاج تفعيل. استخدم رقم الجوال ورمز التفعيل أولًا.", "error")
            return redirect(url_for("user_activate"))
        if verify_portal_password(row.get("password_hash"), password):
            finalize_beneficiary_portal_login(row)
            log_action("beneficiary_login", "beneficiary_portal_account", row["id"], f"Portal login for beneficiary {row['beneficiary_id']}")
            return redirect(url_for("user_dashboard"))
        register_portal_failed_attempt(row["id"])
        flash("بيانات الدخول غير صحيحة.", "error")
        return redirect(url_for("user_login"))
    return render_template("auth/user_login.html")
