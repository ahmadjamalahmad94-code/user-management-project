# Continued split from 40_user_activation_patch_routes.py lines 119-209. Loaded by app.legacy.


def _patched_user_login():
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
    content = """
    <div class="login-wrap">
      <div class="hero"><h1>دخول المستفيد</h1><p>استخدم رقم الجوال وكلمة المرور بعد تفعيل الحساب لأول مرة.</p></div>
      <div class="card">
        <form method="POST">
          <div class="grid grid-2">
            <div><label>رقم الجوال</label><input name="username" required></div>
            <div><label>كلمة المرور</label><input type="password" name="password" required></div>
          </div>
          <div class="actions" style="margin-top:16px">
            <button class="btn btn-primary" type="submit">دخول</button>
            <a class="btn btn-soft" href="/user/activate">تفعيل الحساب</a>
            <a class="btn btn-soft" href="/login">دخول الإدارة</a>
          </div>
        </form>
      </div>
    </div>
    """
    return render_user_page("دخول المستفيد", content)


def _patched_user_profile_page():
    beneficiary = get_current_portal_beneficiary()
    portal_account = query_one(
        "SELECT * FROM beneficiary_portal_accounts WHERE id=%s LIMIT 1",
        [session.get("beneficiary_portal_account_id")],
    )
    if request.method == "POST":
        current_password = clean_csv_value(request.form.get("current_password"))
        new_password = clean_csv_value(request.form.get("new_password"))
        if not verify_portal_password(portal_account.get("password_hash"), current_password):
            flash("كلمة المرور الحالية غير صحيحة.", "error")
            return redirect(url_for("user_profile_page"))
        if len(new_password) < 8:
            flash("كلمة المرور الجديدة يجب أن تكون 8 أحرف على الأقل.", "error")
            return redirect(url_for("user_profile_page"))
        execute_sql(
            "UPDATE beneficiary_portal_accounts SET password_hash=%s, password_plain=%s, updated_at=CURRENT_TIMESTAMP WHERE id=%s",
            [portal_password_hash(new_password), new_password, session.get("beneficiary_portal_account_id")],
        )
        log_action("beneficiary_change_password", "beneficiary_portal_account", session.get("beneficiary_portal_account_id"), "Portal password change")
        flash("تم تحديث كلمة المرور.", "success")
        return redirect(url_for("user_profile_page"))
    content = f"""
    <div class="hero"><div><h1>بياناتي</h1><p>يمكنك هنا مراجعة بياناتك الأساسية وتحديث كلمة المرور الدائمة.</p></div></div>
    <div class="card">
      <div class="grid grid-2">
        <div><label>الاسم</label><input value="{safe(beneficiary.get('full_name'))}" disabled></div>
        <div><label>رقم الجوال</label><input value="{safe(beneficiary.get('phone')) or '-'}" disabled></div>
        <div><label>اسم المستخدم</label><input value="{safe(session.get('beneficiary_username'))}" disabled></div>
        <div><label>النوع</label><input value="{safe(get_type_label(beneficiary.get('user_type')))}" disabled></div>
      </div>
    </div>
    <div class="card" style="margin-top:16px">
      <form method="POST">
        <div class="grid grid-2">
          <div><label>كلمة المرور الحالية</label><input type="password" name="current_password" required></div>
          <div><label>كلمة المرور الجديدة</label><input type="password" name="new_password" required></div>
        </div>
        <div class="actions" style="margin-top:16px"><button class="btn btn-primary" type="submit">تحديث</button></div>
      </form>
    </div>
    """
    return render_user_page("بياناتي", content)
