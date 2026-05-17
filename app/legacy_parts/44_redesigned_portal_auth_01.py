# Auto-split from app/legacy.py lines 9685-10188. Loaded by app.legacy.
BASE_TEMPLATE = _legacy_template_text('44_redesigned_portal_auth.BASE_TEMPLATE.html')


USER_BASE_TEMPLATE = _legacy_template_text('44_redesigned_portal_auth.USER_BASE_TEMPLATE.html')


def render_user_page(title, content):
    beneficiary = get_current_portal_beneficiary() if session.get("portal_type") == "beneficiary" else None
    access_mode = get_beneficiary_access_mode(beneficiary)
    return render_template_string(
        USER_BASE_TEMPLATE,
        title=title,
        content=content,
        portal_access_mode=access_mode,
        portal_access_label=get_beneficiary_access_label(beneficiary),
        portal_copy=portal_access_type_copy(access_mode),
        hebron_now=portal_now_hebron(),
    )


def _redesigned_portal_entry():
    return render_template("auth/portal_entry.html")


def _redesigned_admin_login():
    if session.get("account_id"):
        return redirect(url_for("dashboard"))
    if session.get("portal_type") == "beneficiary" and session.get("beneficiary_id"):
        return redirect(url_for("user_dashboard"))
    if request.method == "POST":
        username = clean_csv_value(request.form.get("username"))
        password = clean_csv_value(request.form.get("password"))
        failure_key = auth_failure_key("admin", username)
        if is_auth_limited(failure_key):
            flash("تم إيقاف محاولات الدخول مؤقتًا. حاول لاحقًا.", "error")
            return redirect(url_for("login"))
        row = query_one(
            """
            SELECT * FROM app_accounts
            WHERE username=%s AND is_active=TRUE
            LIMIT 1
            """,
            [username],
        )
        if row and verify_admin_password(row.get("password_hash"), password):
            maybe_upgrade_admin_password(row["id"], password, row.get("password_hash"))
            clear_auth_failures(failure_key)
            session.clear()
            session["portal_type"] = "admin"
            session["account_id"] = row["id"]
            session["username"] = row["username"]
            session["full_name"] = row["full_name"]
            refresh_session_permissions(row["id"])
            log_action("login", "account", row["id"], "تسجيل دخول")
            return redirect(url_for("dashboard"))
        register_auth_failure(failure_key)
        flash("اسم المستخدم أو كلمة المرور غير صحيحة.", "error")
    return render_template("auth/admin_login.html")
