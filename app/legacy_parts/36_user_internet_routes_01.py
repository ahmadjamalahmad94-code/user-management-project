# Auto-split from app/legacy.py lines 7621-7846. Loaded by app.legacy.
@app.route("/internet/request", methods=["GET", "POST"])
@login_required
@permission_required("submit_internet_requests")
def internet_request_page():
    if request.method == "POST":
        beneficiary_id, request_type, requested_payload = normalize_internet_request_form(request.form)
        if beneficiary_id <= 0:
            flash("يجب اختيار مستفيد صالح.", "error")
            return render_internet_request_form()
        req_id = create_internet_service_request(beneficiary_id, request_type, requested_payload)
        log_action("submit_internet_request", "internet_request", req_id, f"Submit {request_type} for beneficiary {beneficiary_id}")
        flash("تم تسجيل الطلب بنجاح وهو الآن قيد المراجعة.", "success")
        return redirect(url_for("internet_my_requests_page"))
    return render_internet_request_form()


@app.route("/user/login", methods=["GET", "POST"])
def user_login():
    if session.get("portal_type") == "beneficiary" and session.get("beneficiary_id"):
        return redirect(url_for("user_dashboard"))
    if session.get("portal_type") == "admin" and session.get("account_id"):
        return redirect(url_for("dashboard"))
    if request.method == "POST":
        username = clean_csv_value(request.form.get("username"))
        password = clean_csv_value(request.form.get("password"))
        row = get_beneficiary_portal_account_by_username(username)
        if row and row.get("password_hash") == sha256_text(password):
            session.clear()
            session["portal_type"] = "beneficiary"
            session["beneficiary_id"] = row["beneficiary_id"]
            session["beneficiary_portal_account_id"] = row["id"]
            session["beneficiary_username"] = row["username"]
            session["beneficiary_full_name"] = row.get("full_name") or ""
            execute_sql(
                "UPDATE beneficiary_portal_accounts SET last_login_at=CURRENT_TIMESTAMP, updated_at=CURRENT_TIMESTAMP WHERE id=%s",
                [row["id"]],
            )
            log_action("beneficiary_login", "beneficiary_portal_account", row["id"], f"Portal login for beneficiary {row['beneficiary_id']}")
            return redirect(url_for("user_dashboard"))
        flash("بيانات الدخول غير صحيحة.", "error")
    content = """
    <div class="login-wrap">
      <div class="hero"><h1>دخول المستفيد</h1><p>بوابة المستفيدين لعرض الحالة وإرسال طلبات خدمات الإنترنت.</p></div>
      <div class="card">
        <form method="POST">
          <div class="grid grid-2">
            <div><label>اسم المستخدم</label><input name="username" required></div>
            <div><label>كلمة المرور</label><input type="password" name="password" required></div>
          </div>
          <div class="actions" style="margin-top:16px">
            <button class="btn btn-primary" type="submit">دخول</button>
            <a class="btn btn-soft" href="/login">دخول الإدارة</a>
          </div>
        </form>
      </div>
    </div>
    """
    return render_user_page("دخول المستفيد", content)


@app.route("/user/logout")
@user_login_required
def user_logout():
    log_action(
        "beneficiary_logout",
        "beneficiary_portal_account",
        session.get("beneficiary_portal_account_id"),
        f"Portal logout for beneficiary {session.get('beneficiary_id')}",
    )
    session.clear()
    return redirect(url_for("user_login"))


@app.route("/user/dashboard")
@user_login_required
def user_dashboard():
    beneficiary = get_current_portal_beneficiary()
    radius_account = get_user_radius_account() or {}
    requests_rows = get_user_requests()
    pending_count = len([r for r in requests_rows if r.get("status") == "pending"])
    executed_count = len([r for r in requests_rows if r.get("status") == "executed"])
    content = f"""
    <div class="hero"><div><h1>الرئيسية</h1><p>مرحبًا بك في بوابة المستفيدين. هنا ترى بياناتك وحساب الإنترنت وطلباتك فقط.</p></div></div>
    <div class="grid grid-3">
      <div class="stat"><div class="icon"><i class="fa-solid fa-id-card"></i></div><div class="muted">حساب الإنترنت</div><div class="kpi">{safe(radius_account.get('external_username')) or '-'}</div></div>
      <div class="stat"><div class="icon"><i class="fa-solid fa-list-check"></i></div><div class="muted">الطلبات قيد المراجعة</div><div class="kpi">{pending_count}</div></div>
      <div class="stat"><div class="icon"><i class="fa-solid fa-circle-check"></i></div><div class="muted">طلبات تم تنفيذها</div><div class="kpi">{executed_count}</div></div>
    </div>
    <div class="grid grid-2" style="margin-top:16px">
      <div class="card"><h3>بياناتي</h3><div class="grid grid-2"><div><label>الاسم</label><div>{safe(beneficiary.get('full_name'))}</div></div><div><label>الجوال</label><div>{safe(beneficiary.get('phone')) or '-'}</div></div><div><label>النوع</label><div>{safe(get_type_label(beneficiary.get('user_type')))}</div></div><div><label>حالي</label><div>{internet_request_status_pill(radius_account.get('status') or 'pending')}</div></div></div></div>
      <div class="card"><h3>اختصارات</h3><div class="actions"><a class="btn btn-primary" href="{url_for('user_internet_request_page')}">طلب خدمة</a><a class="btn btn-soft" href="{url_for('user_internet_my_requests_page')}">طلباتي</a><a class="btn btn-soft" href="{url_for('user_internet_access_page')}">حساب الإنترنت</a></div></div>
    </div>
    """
    return render_user_page("الرئيسية", content)


@app.route("/user/profile", methods=["GET", "POST"])
@user_login_required
def user_profile_page():
    beneficiary = get_current_portal_beneficiary()
    portal_account = query_one(
        "SELECT * FROM beneficiary_portal_accounts WHERE id=%s LIMIT 1",
        [session.get("beneficiary_portal_account_id")],
    )
    if request.method == "POST":
        current_password = clean_csv_value(request.form.get("current_password"))
        new_password = clean_csv_value(request.form.get("new_password"))
        if portal_account and portal_account.get("password_hash") != sha256_text(current_password):
            flash("كلمة المرور الحالية غير صحيحة.", "error")
            return redirect(url_for("user_profile_page"))
        if not new_password:
            flash("كلمة المرور الجديدة مطلوبة.", "error")
            return redirect(url_for("user_profile_page"))
        execute_sql(
            "UPDATE beneficiary_portal_accounts SET password_hash=%s, password_plain=%s, updated_at=CURRENT_TIMESTAMP WHERE id=%s",
            [sha256_text(new_password), new_password, session.get("beneficiary_portal_account_id")],
        )
        log_action("beneficiary_change_password", "beneficiary_portal_account", session.get("beneficiary_portal_account_id"), "Portal password change")
        flash("تم تحديث كلمة المرور.", "success")
        return redirect(url_for("user_profile_page"))
    content = f"""
    <div class="hero"><div><h1>بياناتي</h1><p>يمكنك هنا مراجعة بياناتك الأساسية وتحديث كلمة مرور بوابة المستفيد.</p></div></div>
    <div class="card">
      <div class="grid grid-2">
        <div><label>الاسم</label><input value="{safe(beneficiary.get('full_name'))}" disabled></div>
        <div><label>الجوال</label><input value="{safe(beneficiary.get('phone')) or '-'}" disabled></div>
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
