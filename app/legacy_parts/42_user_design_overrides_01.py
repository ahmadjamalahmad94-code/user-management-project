# Auto-split from app/legacy.py lines 9107-9583. Loaded by app.legacy.
def _designed_user_login():
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
    <section class="portal-auth-hero">
      <div>
        <span class="badge badge-blue">بوابة المشتركين</span>
        <h1>تسجيل دخول المشترك</h1>
        <p>ادخل برقم الجوال وكلمة المرور بعد تفعيل الحساب. ستنتقل بعدها إلى واجهة المشترك المناسبة لنوع خدمتك.</p>
      </div>
      <div class="portal-feature-list">
        <div><i class="fa-solid fa-gauge-high"></i><span>متابعة الحالة والطلبات</span></div>
        <div><i class="fa-solid fa-user-shield"></i><span>معزولة عن لوحة الإدارة</span></div>
        <div><i class="fa-solid fa-clock"></i><span>مصممة لخدمات الإنترنت المجانية</span></div>
      </div>
    </section>
    <div class="portal-panel portal-auth-panel">
      <form method="POST">
        <div class="grid grid-2">
          <div><label>رقم الجوال</label><input name="username" required></div>
          <div><label>كلمة المرور</label><input type="password" name="password" required></div>
        </div>
        <div class="actions" style="margin-top:16px">
          <button class="btn btn-primary" type="submit">تسجيل الدخول</button>
          <a class="btn btn-soft" href="/user/activate">تفعيل الحساب</a>
          <a class="btn btn-soft" href="/user/register">تسجيل اشتراك</a>
          <a class="btn btn-soft" href="/login">دخول الإدارة</a>
        </div>
      </form>
    </div>
    """
    return render_user_page("تسجيل دخول المشترك", content)


def _designed_user_dashboard():
    beneficiary = get_current_portal_beneficiary()
    radius_account = get_user_radius_account() or {}
    requests_rows = get_user_requests()
    access_mode = get_beneficiary_access_mode(beneficiary)
    workday = portal_workday_context()
    pending_count = len([r for r in requests_rows if r.get("status") == "pending"])
    executed_count = len([r for r in requests_rows if r.get("status") == "executed"])
    failed_count = len([r for r in requests_rows if r.get("status") in {"failed", "rejected"}])
    hero_note = "الدوام ينتهي عند الرابعة مساءً بتوقيت الخليل." if workday["is_open"] else "انتهى دوام اليوم، وسيظهر تقييم الطلبات في اليوم التالي."
    if access_mode == "cards":
        cards_html = "".join(
            f"<div class='mini-option {'available' if item['available'] else 'blocked'}'><strong>{item['label']}</strong><span>{item['minutes']} دقيقة</span></div>"
            for item in portal_card_options()
        )
        content = f"""
        <section class="portal-hero-card">
          <div>
            <span class="badge badge-blue">مشترك بطاقات</span>
            <h1>مرحبًا {safe(beneficiary.get('full_name'))}</h1>
            <p>{hero_note} الحدود الأسبوعية تتجدد كل جمعة، ويتم تجهيز طلبك حسب الوقت المتبقي للدوام.</p>
          </div>
          <div class="summary-grid">
            <div class="summary-card"><div class="label">الطلبات المعلقة</div><div class="value">{pending_count}</div><div class="note">الطلبات التي تنتظر المراجعة</div></div>
            <div class="summary-card"><div class="label">بطاقات معتمدة</div><div class="value">{executed_count}</div><div class="note">طلبات تم تنفيذها سابقًا</div></div>
            <div class="summary-card"><div class="label">إعادة التجديد</div><div class="value">{portal_next_friday_date().strftime('%Y-%m-%d')}</div><div class="note">كل جمعة</div></div>
          </div>
        </section>
        <div class="grid grid-2" style="margin-top:18px">
          <div class="portal-panel">
            <div class="section-heading"><div><h3>الخيارات المتاحة اليوم</h3><p>تحدد حسب الوقت المتبقي حتى الرابعة.</p></div></div>
            <div class="mini-option-grid">{cards_html}</div>
            <div class="info-note" style="margin-top:14px">الوقت المتبقي للدوام: <strong>{workday['remaining_minutes']} دقيقة</strong></div>
          </div>
          <div class="portal-panel">
            <div class="section-heading"><div><h3>اختصارات سريعة</h3><p>انتقل مباشرة للطلب أو لمتابعة حالة الطلبات.</p></div></div>
            <div class="request-actions">
              <a class="btn btn-primary" href="{url_for('user_internet_request_page')}">طلب بطاقة</a>
              <a class="btn btn-soft" href="{url_for('user_internet_my_requests_page')}">طلباتي</a>
              <a class="btn btn-soft" href="{url_for('user_profile_page')}">ملفي الشخصي</a>
            </div>
            <div class="empty-state-card" style="margin-top:14px">هذه الواجهة مخصصة للبطاقات الأسبوعية فقط، ولا تعرض خيارات اليوزر غير المرتبطة بحالتك.</div>
          </div>
        </div>
        """
        return render_user_page("الرئيسية", content)
    content = f"""
    <section class="portal-hero-card">
      <div>
        <span class="badge badge-blue">مشترك يوزر</span>
        <h1>مرحبًا {safe(beneficiary.get('full_name'))}</h1>
        <p>{hero_note} هنا تملك واجهة مختصرة لحساب الإنترنت وطلبات الخدمات المرتبطة به.</p>
      </div>
      <div class="summary-grid">
        <div class="summary-card"><div class="label">اسم المستخدم الخارجي</div><div class="value">{safe(radius_account.get('external_username')) or '-'}</div><div class="note">الربط المحلي لحسابك</div></div>
        <div class="summary-card"><div class="label">طلبات قيد المراجعة</div><div class="value">{pending_count}</div><div class="note">بانتظار الاعتماد</div></div>
        <div class="summary-card"><div class="label">مشاكل تحتاج متابعة</div><div class="value">{failed_count}</div><div class="note">فشل أو رفض</div></div>
      </div>
    </section>
    <div class="grid grid-2" style="margin-top:18px">
      <div class="portal-panel">
        <div class="section-heading"><div><h3>ملخص حساب الإنترنت</h3><p>أهم بيانات الحساب المرتبط بك.</p></div></div>
        <div class="summary-grid">
          <div class="summary-card"><div class="label">الحالة</div><div class="value" style="font-size:18px">{internet_request_status_pill(radius_account.get('status') or 'pending')}</div></div>
          <div class="summary-card"><div class="label">البروفايل</div><div class="value" style="font-size:18px">{safe(radius_account.get('current_profile_name')) or safe(radius_account.get('current_profile_id')) or '-'}</div></div>
        </div>
      </div>
      <div class="portal-panel">
        <div class="section-heading"><div><h3>اختصارات سريعة</h3><p>اختر الإجراء الذي تحتاجه دون الدخول إلى شاشات كثيرة.</p></div></div>
        <div class="request-actions">
          <a class="btn btn-primary" href="{url_for('user_internet_access_page')}">حساب الإنترنت</a>
          <a class="btn btn-soft" href="{url_for('user_internet_request_page')}">طلب خدمة</a>
          <a class="btn btn-soft" href="{url_for('user_internet_my_requests_page')}">طلباتي</a>
        </div>
      </div>
    </div>
    """
    return render_user_page("الرئيسية", content)
