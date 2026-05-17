# Auto-split from app/legacy.py lines 3459-3743. Loaded by app.legacy.
def normalize_beneficiary_usage(user_id):
    row = query_one("SELECT weekly_usage_week_start FROM beneficiaries WHERE id=%s", [user_id])
    if not row:
        return
    current_start = get_week_start()
    saved = row["weekly_usage_week_start"]
    if saved != current_start:
        execute_sql("""
            UPDATE beneficiaries
            SET weekly_usage_count = 0, weekly_usage_week_start = %s
            WHERE id = %s
        """, [current_start, user_id])


def normalize_all_usage():
    execute_sql("""
        UPDATE beneficiaries
        SET weekly_usage_count = 0, weekly_usage_week_start = %s
        WHERE weekly_usage_week_start IS DISTINCT FROM %s
    """, [get_week_start(), get_week_start()])


@app.route("/")
def root():
    if session.get("portal_type") == "beneficiary" and session.get("beneficiary_id"):
        return redirect(url_for("user_dashboard"))
    if session.get("account_id"):
        return redirect(url_for("dashboard"))
    return redirect(url_for("portal_entry"))


@app.route("/portal")
def portal_entry():
    css_href = url_for("static", filename="css/base.css")
    content = f"""
    <!DOCTYPE html>
    <html lang="ar" dir="rtl">
    <head>
      <meta charset="UTF-8">
      <meta name="viewport" content="width=device-width, initial-scale=1.0">
      <title>{"\u0628\u0648\u0627\u0628\u0629 Hobe Hub"}</title>
      <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
      <link rel="stylesheet" href="{css_href}">
    </head>
    <body class="portal-auth-body">
      <div class="portal-auth-shell" style="max-width:1240px;padding-top:42px">
        <section class="portal-auth-hero">
          <div>
            <span class="badge badge-blue">{"\u0645\u0646\u0635\u0629 \u0625\u062f\u0627\u0631\u0629 \u0648\u062e\u062f\u0645\u0627\u062a \u0625\u0646\u062a\u0631\u0646\u062a"}</span>
            <h1>{"\u0648\u0627\u062c\u0647\u0629 \u0627\u0646\u0637\u0644\u0627\u0642 Hobe Hub"}</h1>
            <p>{"\u0645\u062f\u062e\u0644 \u0648\u0627\u0636\u062d \u0648\u0647\u0627\u062f\u0626 \u0625\u0644\u0649 \u0644\u0648\u062d\u0629 \u0627\u0644\u0625\u062f\u0627\u0631\u0629 \u0648\u0628\u0648\u0627\u0628\u0629 \u0627\u0644\u0645\u0634\u062a\u0631\u0643\u064a\u0646. \u064a\u0645\u0643\u0646\u0643 \u0645\u0646 \u0647\u0646\u0627 \u0627\u0644\u062f\u062e\u0648\u0644 \u0643\u0625\u062f\u0627\u0631\u0629\u060c \u0623\u0648 \u062a\u0633\u062c\u064a\u0644 \u062f\u062e\u0648\u0644 \u0645\u0634\u062a\u0631\u0643\u060c \u0623\u0648 \u0627\u0644\u0628\u062f\u0621 \u0628\u0637\u0644\u0628 \u0627\u0634\u062a\u0631\u0627\u0643 \u062c\u062f\u064a\u062f."}</p>
          </div>
          <div class="portal-feature-list">
            <div><i class="fa-solid fa-user-shield"></i><span>{"\u0644\u0648\u062d\u0629 \u062a\u062d\u0643\u0645 \u0627\u0644\u0625\u062f\u0627\u0631\u0629 \u0644\u0644\u062a\u0634\u063a\u064a\u0644 \u0648\u0627\u0644\u0645\u062a\u0627\u0628\u0639\u0629"}</span></div>
            <div><i class="fa-solid fa-users"></i><span>{"\u0628\u0648\u0627\u0628\u0629 \u0645\u0634\u062a\u0631\u0643\u064a\u0646 \u0645\u0646\u0641\u0635\u0644\u0629 \u0648\u0648\u0627\u0636\u062d\u0629"}</span></div>
            <div><i class="fa-solid fa-wifi"></i><span>{"\u062e\u062f\u0645\u0627\u062a \u064a\u0648\u0632\u0631 \u0648\u0628\u0637\u0627\u0642\u0627\u062a \u0636\u0645\u0646 \u0646\u0641\u0633 \u0627\u0644\u0645\u0646\u0635\u0629"}</span></div>
          </div>
        </section>
        <div class="summary-grid">
          <a class="entry-card" href="/user/login">
            <span class="entry-icon"><i class="fa-solid fa-right-to-bracket"></i></span>
            <strong>{"\u062a\u0633\u062c\u064a\u0644 \u062f\u062e\u0648\u0644 \u0645\u0634\u062a\u0631\u0643"}</strong>
            <p>{"\u062f\u062e\u0648\u0644 \u0645\u0628\u0627\u0634\u0631 \u0625\u0644\u0649 \u0628\u0648\u0627\u0628\u0629 \u0627\u0644\u0645\u0634\u062a\u0631\u0643 \u0648\u0645\u062a\u0627\u0628\u0639\u0629 \u0627\u0644\u062d\u0633\u0627\u0628 \u0623\u0648 \u0627\u0644\u0637\u0644\u0628\u0627\u062a."}</p>
          </a>
          <a class="entry-card" href="/user/register">
            <span class="entry-icon"><i class="fa-solid fa-user-plus"></i></span>
            <strong>{"\u062a\u0633\u062c\u064a\u0644 \u0627\u0634\u062a\u0631\u0627\u0643 \u0645\u0634\u062a\u0631\u0643"}</strong>
            <p>{"\u0648\u0627\u062c\u0647\u0629 \u0623\u0648\u0644\u064a\u0629 \u0646\u0627\u0639\u0645\u0629 \u0644\u062a\u062c\u0647\u064a\u0632 \u0637\u0644\u0628 \u0627\u0634\u062a\u0631\u0627\u0643 \u062c\u062f\u064a\u062f \u062f\u0627\u062e\u0644 \u0627\u0644\u0645\u0631\u0643\u0632."}</p>
          </a>
          <a class="entry-card" href="/login">
            <span class="entry-icon"><i class="fa-solid fa-sliders"></i></span>
            <strong>{"\u0644\u0648\u062d\u0629 \u062a\u062d\u0643\u0645 \u0627\u0644\u0625\u062f\u0627\u0631\u0629"}</strong>
            <p>{"\u0627\u0644\u062f\u062e\u0648\u0644 \u0625\u0644\u0649 \u0627\u0644\u0646\u0638\u0627\u0645 \u0627\u0644\u0625\u062f\u0627\u0631\u064a \u0644\u0625\u062f\u0627\u0631\u0629 \u0627\u0644\u0645\u0634\u062a\u0631\u0643\u064a\u0646 \u0648\u0627\u0644\u0637\u0644\u0628\u0627\u062a \u0648\u0627\u0644\u0631\u0628\u0637."}</p>
          </a>
        </div>
      </div>
    </body>
    </html>
    """
    return render_template_string(content)


@app.route("/login", methods=["GET", "POST"])
def login():
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
        row = query_one("""
            SELECT * FROM app_accounts
            WHERE username=%s AND is_active=TRUE
            LIMIT 1
        """, [username])
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
    content = """
    <div class="login-wrap">
      <div id="dashboard-live-root" class="hero">
        <h1>تسجيل الدخول</h1>
      </div>
      <div class="card">
        <form method="POST">
          <div class="row">
            <div><label>اسم المستخدم</label><input name="username" required></div>
            <div><label>كلمة المرور</label><input type="password" name="password" required></div>
          </div>
          <div class="actions" style="margin-top:4px">
            <button class="btn btn-primary" type="submit">دخول</button>
          </div>
        </form>
      </div>
    </div>
    """
    return render_page("تسجيل الدخول", content)


@app.route("/logout")
@login_required
def logout():
    log_action("logout", "account", session.get("account_id"), "تسجيل خروج")
    session.clear()
    return redirect(url_for("login"))


def get_type_label(user_type=None):
    return {
        "tawjihi": "توجيهي",
        "university": "جامعة",
        "freelancer": "فري لانسر",
    }.get(user_type, safe(user_type or ""))


def get_type_css(user_type=None):
    return {
        "tawjihi": "type-green",
        "university": "type-purple",
        "freelancer": "type-blue",
    }.get(user_type, "type-default")


from app.dashboard import services as _dashboard_services


def normalize_beneficiary_usage(user_id):
    return _dashboard_services.normalize_beneficiary_usage(user_id, get_week_start())


def normalize_all_usage():
    return _dashboard_services.normalize_all_usage(get_week_start())


get_type_label = _dashboard_services.get_type_label
get_type_css = _dashboard_services.get_type_css
