# Continued split from 27_account_routes.py lines 127-244. Loaded by app.legacy.


@app.route("/accounts/edit/<int:account_id>", methods=["GET", "POST"])
@login_required
@permission_required("manage_accounts")
def edit_account(account_id):
    row = query_one("SELECT * FROM app_accounts WHERE id=%s", [account_id])
    if not row:
        flash("الحساب غير موجود.", "error")
        return redirect(url_for("accounts_page"))
    assigned = query_all("""
        SELECT p.name
        FROM account_permissions ap
        JOIN permissions p ON p.id = ap.permission_id
        WHERE ap.account_id=%s
    """, [account_id])
    assigned_names = [x["name"] for x in assigned]
    if request.method == "POST":
        username = clean_csv_value(request.form.get("username"))
        full_name = clean_csv_value(request.form.get("full_name"))
        password = clean_csv_value(request.form.get("password"))
        perms = request.form.getlist("permissions")
        try:
            execute_sql("UPDATE app_accounts SET username=%s, full_name=%s WHERE id=%s", [username, full_name, account_id])
        except psycopg2.Error:
            flash("تعذر تحديث الحساب. تأكد أن اسم المستخدم غير مكرر.", "error")
            return redirect(url_for("edit_account", account_id=account_id))
        if password:
            execute_sql("UPDATE app_accounts SET password_hash=%s WHERE id=%s", [admin_password_hash(password), account_id])
        execute_sql("DELETE FROM account_permissions WHERE account_id=%s", [account_id])
        for p in perms:
            execute_sql("""
                INSERT INTO account_permissions (account_id, permission_id)
                SELECT %s, id FROM permissions WHERE name=%s
                ON CONFLICT DO NOTHING
            """, [account_id, p])
        if session.get("account_id") == account_id:
            session["username"] = username
            session["full_name"] = full_name
            refresh_session_permissions(account_id)
        log_action("edit_account", "account", account_id, f"تعديل حساب {username}")
        flash("تم تحديث الحساب.", "success")
        return redirect(url_for("accounts_page"))
    content = f"""
    <div class="hero"><h1>تعديل مستخدم</h1><p>تعديل البيانات والصلاحيات وإعادة تعيين كلمة المرور عند الحاجة.</p></div>
    <div class="card">
      <form method="POST">
        <div class="row">
          <div><label>اسم المستخدم</label><input name="username" value="{safe(row['username'])}" required></div>
          <div><label>كلمة المرور الجديدة</label><input type="password" name="password" placeholder="اتركها فارغة بدون تغيير"></div>
          <div><label>الاسم الكامل</label><input name="full_name" value="{safe(row['full_name'])}"></div>
        </div>
        <div style="margin-top:14px">
          <label>الصلاحيات</label>
          {permissions_checkboxes(assigned_names)}
        </div>
        <div class="actions" style="margin-top:4px">
          <button class="btn btn-primary" type="submit">حفظ التعديلات</button>
          <a class="btn btn-outline" href="{url_for('accounts_page')}">رجوع</a>
        </div>
      </form>
    </div>
    """
    return render_page("تعديل مستخدم", content)


@app.route("/accounts/toggle/<int:account_id>", methods=["POST"])
@login_required
@permission_required("manage_accounts")
def toggle_account(account_id):
    execute_sql("UPDATE app_accounts SET is_active = NOT is_active WHERE id=%s", [account_id])
    log_action("toggle_account", "account", account_id, "تفعيل/تعطيل حساب")
    flash("تم تحديث حالة الحساب.", "success")
    return redirect(url_for("accounts_page"))


@app.route("/profile", methods=["GET", "POST"])
@login_required
def profile_page():
    row = query_one("SELECT * FROM app_accounts WHERE id=%s", [session["account_id"]])
    perms = query_all("""
        SELECT p.name FROM account_permissions ap
        JOIN permissions p ON p.id = ap.permission_id
        WHERE ap.account_id=%s
        ORDER BY p.name
    """, [session["account_id"]])
    if request.method == "POST":
        current_password = clean_csv_value(request.form.get("current_password"))
        new_password = clean_csv_value(request.form.get("new_password"))
        full_name = clean_csv_value(request.form.get("full_name"))
        if not verify_admin_password(row.get("password_hash"), current_password):
            flash("كلمة المرور الحالية غير صحيحة.", "error")
            return redirect(url_for("profile_page"))
        if not new_password:
            flash("كلمة المرور الجديدة مطلوبة.", "error")
            return redirect(url_for("profile_page"))
        execute_sql("UPDATE app_accounts SET full_name=%s, password_hash=%s WHERE id=%s", [full_name, admin_password_hash(new_password), session["account_id"]])
        session["full_name"] = full_name
        log_action("change_password", "account", session["account_id"], "تغيير كلمة المرور من الصفحة الشخصية")
        flash("تم تحديث بياناتك وكلمة المرور.", "success")
        return redirect(url_for("profile_page"))
    perm_html = "".join([f"<span class='badge'>{p['name']}</span> " for p in perms]) or "<span class='small'>لا توجد صلاحيات.</span>"
    content = f"""
    <div class="hero"><h1>صفحتي الشخصية</h1><p>تعديل الاسم الكامل وكلمة المرور.</p></div>
    <div class="card">
      <div class="small" style="margin-bottom:10px">الصلاحيات الحالية: {perm_html}</div>
      <form method="POST">
        <div class="row">
          <div><label>اسم المستخدم</label><input value="{safe(row['username'])}" disabled></div>
          <div><label>الاسم الكامل</label><input name="full_name" value="{safe(row['full_name'])}"></div>
          <div><label>كلمة المرور الحالية</label><input type="password" name="current_password" required></div>
          <div><label>كلمة المرور الجديدة</label><input type="password" name="new_password" required></div>
        </div>
        <div class="actions" style="margin-top:4px"><button class="btn btn-primary" type="submit">حفظ</button></div>
      </form>
    </div>
    """
    return render_page("صفحتي الشخصية", content)
