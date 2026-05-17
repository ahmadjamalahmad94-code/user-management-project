# Auto-split from app/legacy.py lines 8530-8863. Loaded by app.legacy.
@app.route("/user/activate", methods=["GET", "POST"])
def user_activate():
    if session.get("portal_type") == "beneficiary" and session.get("beneficiary_id"):
        return redirect(url_for("user_dashboard"))
    if request.method == "POST":
        username = normalize_portal_username(request.form.get("username"))
        code = clean_csv_value(request.form.get("activation_code"))
        row = get_beneficiary_portal_account_by_username(username)
        if not row:
            flash("بيانات التفعيل غير صحيحة.", "error")
            return redirect(url_for("user_activate"))
        if portal_account_is_locked(row):
            flash("تم إيقاف المحاولة مؤقتًا. يرجى الانتظار ثم إعادة المحاولة.", "error")
            return redirect(url_for("user_activate"))
        expires_at = as_local_dt(row.get("activation_code_expires_at"))
        if not row.get("activation_code_hash") or not expires_at or expires_at < now_local():
            register_portal_failed_attempt(row["id"])
            flash("رمز التفعيل غير صالح أو منتهي الصلاحية.", "error")
            return redirect(url_for("user_activate"))
        if activation_code_hash(code) != row.get("activation_code_hash"):
            register_portal_failed_attempt(row["id"])
            flash("رمز التفعيل غير صحيح.", "error")
            return redirect(url_for("user_activate"))
        clear_portal_failed_attempts(row["id"])
        session.clear()
        session["pending_password_setup_account_id"] = row["id"]
        session["pending_password_setup_beneficiary_id"] = row["beneficiary_id"]
        session["pending_password_setup_username"] = row["username"]
        session["pending_password_setup_full_name"] = row.get("full_name") or ""
        return redirect(url_for("user_set_password"))
    return render_template("auth/user_activate.html")


@app.route("/user/set-password", methods=["GET", "POST"])
def user_set_password():
    account_id = int(session.get("pending_password_setup_account_id") or 0)
    if account_id <= 0:
        flash("يجب تفعيل الحساب أولًا.", "error")
        return redirect(url_for("user_activate"))
    row = query_one(
        """
        SELECT pa.*, b.full_name, b.phone
        FROM beneficiary_portal_accounts pa
        JOIN beneficiaries b ON b.id = pa.beneficiary_id
        WHERE pa.id=%s LIMIT 1
        """,
        [account_id],
    )
    if not row:
        session.pop("pending_password_setup_account_id", None)
        flash("تعذر متابعة تفعيل الحساب.", "error")
        return redirect(url_for("user_activate"))
    if request.method == "POST":
        new_password = clean_csv_value(request.form.get("new_password"))
        confirm_password = clean_csv_value(request.form.get("confirm_password"))
        if len(new_password) < 8:
            flash("كلمة المرور الجديدة يجب أن تكون 8 أحرف على الأقل.", "error")
            return redirect(url_for("user_set_password"))
        if new_password != confirm_password:
            flash("تأكيد كلمة المرور غير مطابق.", "error")
            return redirect(url_for("user_set_password"))
        execute_sql(
            """
            UPDATE beneficiary_portal_accounts
            SET password_hash=%s,
                password_plain=%s,
                must_set_password=FALSE,
                activation_code_hash=NULL,
                activation_code_expires_at=NULL,
                activated_at=CURRENT_TIMESTAMP,
                failed_login_attempts=0,
                locked_until=NULL,
                updated_at=CURRENT_TIMESTAMP
            WHERE id=%s
            """,
            [portal_password_hash(new_password), new_password, account_id],
        )
        session.pop("pending_password_setup_account_id", None)
        session.pop("pending_password_setup_beneficiary_id", None)
        session.pop("pending_password_setup_username", None)
        session.pop("pending_password_setup_full_name", None)
        row["username"] = row["username"]
        finalize_beneficiary_portal_login(row)
        log_action("beneficiary_activate_account", "beneficiary_portal_account", row["id"], "Portal activation completed")
        flash("تم تعيين كلمة المرور وتفعيل الحساب بنجاح.", "success")
        return redirect(url_for("user_dashboard"))
    content = f"""
    <div class="login-wrap">
      <div class="hero"><h1>تعيين كلمة المرور</h1><p>مرحبًا {safe(row.get('full_name'))}. هذه الخطوة مطلوبة لأول دخول.</p></div>
      <div class="card">
        <form method="POST">
          <div class="grid grid-2">
            <div><label>كلمة المرور الجديدة</label><input type="password" name="new_password" required></div>
            <div><label>تأكيد كلمة المرور</label><input type="password" name="confirm_password" required></div>
          </div>
          <div class="actions" style="margin-top:16px"><button class="btn btn-primary" type="submit">تعيين كلمة المرور</button></div>
        </form>
      </div>
    </div>
    """
    return render_user_page("تعيين كلمة المرور", content)
