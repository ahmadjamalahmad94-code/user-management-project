# Auto-split from app/legacy.py lines 8307-8527. Loaded by app.legacy.
@app.route("/admin/radius/settings", methods=["GET", "POST"])
@login_required
@permission_required("manage_radius_settings")
def radius_settings_page():
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
            SET base_url=%s, admin_username=%s, service_username=%s, api_enabled=%s, updated_at=CURRENT_TIMESTAMP
            WHERE id=%s
            """,
            [base_url, admin_username, service_username, api_enabled, settings_row["id"]],
        )
        log_action("update_radius_settings", "radius_settings", settings_row["id"], f"base_url={base_url} enabled={api_enabled}")
        settings_row = get_radius_settings_row()
        if action == "test":
            try:
                client = get_radius_client()
                client.login(force=True)
                test_message = "تم اختبار الاتصال وتسجيل الدخول الخارجي بنجاح."
                test_category = "success"
            except Exception as exc:
                test_message = f"فشل اختبار الاتصال: {safe(str(exc))}"
                test_category = "error"
        else:
            flash("تم حفظ الإعدادات المحلية. مفاتيح API الحساسة تقرأ من متغيرات البيئة.", "success")
            return redirect(url_for("radius_settings_page"))
    env_status = {
        "base": bool(os.getenv("RADIUS_API_BASE_URL")),
        "master": bool(os.getenv("RADIUS_API_MASTER_KEY")),
        "user": bool(os.getenv("RADIUS_API_USERNAME")),
        "password": bool(os.getenv("RADIUS_API_PASSWORD")),
        "app_base": bool(os.getenv("ADV_APP_API_BASE_URL") or os.getenv("ADVRADIUS_APP_BASE_URL")),
        "app_user": bool(os.getenv("ADV_APP_DEFAULT_USERNAME") or os.getenv("ADVRADIUS_APP_USERNAME")),
        "app_password": bool(os.getenv("ADV_APP_DEFAULT_PASSWORD") or os.getenv("ADVRADIUS_APP_PASSWORD")),
    }
    content = f"""
    <div class='hero'><div><h1>إعدادات RADIUS</h1><p>تخزين الرابط العام محليًا، وقراءة الأسرار من متغيرات البيئة فقط.</p></div></div>
    {f"<div class='flash {test_category}'>{test_message}</div>" if test_message else ""}
    <div class='grid grid-2'>
      <div class='card'>
        <form method='POST'>
          <input type='hidden' name='action' value='save'>
          <div class='grid grid-2'>
            <div><label>Base URL</label><input name='base_url' value='{safe(settings_row.get("base_url"))}' placeholder='https://host/app_ad'></div>
            <div><label>اسم المستخدم الإداري</label><input name='admin_username' value='{safe(settings_row.get("admin_username"))}'></div>
            <div><label>اسم مستخدم الخدمة</label><input name='service_username' value='{safe(settings_row.get("service_username"))}'></div>
            <div><label>تفعيل التكامل</label><select name='api_enabled'><option value='1' {'selected' if settings_row.get("api_enabled") else ''}>مفعل</option><option value='0' {'selected' if not settings_row.get("api_enabled") else ''}>متوقف</option></select></div>
          </div>
          <div class='actions' style='margin-top:16px'><button class='btn btn-primary' type='submit'>حفظ</button></div>
        </form>
      </div>
      <div class='card'>
        <h3>حالة متغيرات البيئة</h3>
        <div class='grid grid-2'>
          <div><label>رابط الخدمة الخارجي</label><div>{'موجود' if env_status['base'] else 'غير موجود'}</div></div>
          <div><label>مفتاح الربط الخارجي</label><div>{'موجود' if env_status['master'] else 'غير موجود'}</div></div>
          <div><label>اسم مستخدم الخدمة</label><div>{'موجود' if env_status['user'] else 'غير موجود'}</div></div>
          <div><label>كلمة مرور الخدمة</label><div>{'موجود' if env_status['password'] else 'غير موجود'}</div></div>
        </div>
        <form method='POST' style='margin-top:16px'>
          <input type='hidden' name='action' value='test'>
          <input type='hidden' name='base_url' value='{safe(settings_row.get("base_url"))}'>
          <input type='hidden' name='admin_username' value='{safe(settings_row.get("admin_username"))}'>
          <input type='hidden' name='service_username' value='{safe(settings_row.get("service_username"))}'>
          <input type='hidden' name='api_enabled' value='{"1" if settings_row.get("api_enabled") else "0"}'>
          <button class='btn btn-secondary' type='submit'>اختبار الاتصال</button>
        </form>
        <hr style='margin:18px 0;border:none;border-top:1px solid #e5e7eb'>
        <h3>AdvRadius App API</h3>
        <div class='grid grid-2'>
          <div><label>Base URL</label><div>{safe(os.getenv("ADV_APP_API_BASE_URL") or os.getenv("ADVRADIUS_APP_BASE_URL") or "http://advrapp.com:6950/app")}</div></div>
          <div><label>اسم مستخدم التطبيق</label><div>{'موجود' if env_status['app_user'] else 'غير موجود'}</div></div>
          <div><label>كلمة مرور التطبيق</label><div>{'موجود' if env_status['app_password'] else 'غير موجود'}</div></div>
          <div><label>تعريف قاعدة التطبيق</label><div>{'موجود' if env_status['app_base'] else 'الافتراضي مستخدم'}</div></div>
        </div>
        <form method='POST' action='{url_for("advradius_app_test_route")}' style='margin-top:16px'>
          <button class='btn btn-accent' type='submit'>اختبار Login + Details للتطبيق</button>
        </form>
      </div>
    </div>
    """
    return render_page("إعدادات RADIUS", content)


@app.route("/admin/radius/app-test", methods=["GET", "POST"])
@login_required
@permission_required("manage_radius_settings")
def advradius_app_test_route():
    if request.method == "GET":
        content = f"""
        <div class='hero'>
          <div><h1>اختبار API التطبيق</h1><p>من هذه الصفحة يمكن تنفيذ اختبار للربط مع واجهة التطبيق دون الخروج من لوحة الإدارة.</p></div>
        </div>
        <div class='card'>
          <p class='small'>سيتم تجريب <code>/login</code> ثم <code>/details</code> باستخدام بيانات البيئة الحالية.</p>
          <form method='POST' style='margin-top:16px'>
            <button class='btn btn-accent' type='submit'>تشغيل الاختبار الآن</button>
            <a class='btn btn-soft' href='{url_for("radius_settings_page")}'>العودة إلى إعدادات RADIUS</a>
          </form>
        </div>
        """
        return render_page("اختبار API التطبيق", content)
    try:
        result = test_advradius_app_connection()
        log_action(
            "test_advradius_app_api",
            "radius_settings",
            None,
            f"AdvRadius App API ok account={json.dumps(result.get('account') or {}, ensure_ascii=False)}",
        )
        content = f"""
        <div class='hero'>
          <div><h1>اختبار AdvRadius App API</h1><p>تم تنفيذ /login ثم /details باستخدام ترويسة adv_auth.</p></div>
          <div class='actions'><a class='btn btn-soft' href='{url_for("radius_settings_page")}'>رجوع</a></div>
        </div>
        <div class='grid grid-2'>
          <div class='card'><h3>بيانات الحساب</h3><pre>{safe(json.dumps(result.get("account") or {}, ensure_ascii=False, indent=2))}</pre></div>
          <div class='card'><h3>استجابة /details</h3><pre>{safe(json.dumps(result.get("details") or {}, ensure_ascii=False, indent=2))}</pre></div>
        </div>
        """
        return render_page("اختبار AdvRadius App API", content)
    except Exception as exc:
        log_action("test_advradius_app_api_failed", "radius_settings", None, str(exc))
        flash(f"فشل اختبار AdvRadius App API: {safe(str(exc))}", "error")
        return redirect(url_for("radius_settings_page"))
