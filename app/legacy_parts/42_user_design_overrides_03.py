# Continued split from 42_user_design_overrides.py lines 283-411. Loaded by app.legacy.


def _designed_user_internet_my_requests_page():
    rows = get_user_requests()
    cards = ""
    for row in rows:
        payload = json_safe_dict(row.get("requested_payload"))
        cards += f"""
        <article class="request-card">
          <div class="request-card-header">
            <div>
              {internet_request_type_badge(row.get('request_type'))}
              <div class="small" style="margin-top:8px">طلب #{row['id']} - {format_dt_short(row.get('created_at'))}</div>
            </div>
            <div class="request-card-meta">{internet_request_status_pill(row.get('status'))}</div>
          </div>
          {internet_request_timeline_html(row.get('status'))}
          <div class="request-card-grid" style="margin-top:14px">
            <div><label>النوع</label><div>{safe(internet_request_type_label(row.get('request_type')))}</div></div>
            <div><label>الخلاصة</label><div>{request_payload_summary(payload)}</div></div>
            <div><label>ملاحظة التنفيذ</label><div>{safe(row.get('error_message')) or '-'}</div></div>
          </div>
        </article>
        """
    content = f"""
    <section class="portal-hero-card compact">
      <div>
        <span class="badge badge-blue">طلباتي</span>
        <h1>متابعة حالة الطلبات</h1>
        <p>هنا ترى طلباتك بتسلسل واضح: قيد المراجعة، تمت الموافقة، تم التنفيذ، أو فشل التنفيذ.</p>
      </div>
    </section>
    <div class="summary-grid" style="margin-bottom:16px">
      <div class="summary-card"><div class="label">جميع الطلبات</div><div class="value">{len(rows)}</div></div>
      <div class="summary-card"><div class="label">المعلقة</div><div class="value">{len([r for r in rows if r.get('status') == 'pending'])}</div></div>
      <div class="summary-card"><div class="label">المنفذة</div><div class="value">{len([r for r in rows if r.get('status') == 'executed'])}</div></div>
    </div>
    {cards or "<div class='empty-state-card'>لا يوجد طلبات حاليًا. يمكنك البدء من صفحة طلب الخدمة.</div>"}
    """
    return render_user_page("طلباتي", content)


def _designed_user_profile_page():
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
    <section class="portal-hero-card compact">
      <div>
        <span class="badge badge-blue">ملفي الشخصي</span>
        <h1>بيانات المشترك</h1>
        <p>مراجعة بياناتك الأساسية وتحديث كلمة مرور بوابة المشترك.</p>
      </div>
    </section>
    <div class="grid grid-2">
      <div class="portal-panel">
        <div class="grid grid-2">
          <div><label>الاسم</label><input value="{safe(beneficiary.get('full_name'))}" disabled></div>
          <div><label>رقم الجوال</label><input value="{safe(beneficiary.get('phone')) or '-'}" disabled></div>
          <div><label>اسم المستخدم</label><input value="{safe(session.get('beneficiary_username'))}" disabled></div>
          <div><label>نوع الوصول</label><input value="{safe(get_beneficiary_access_label(beneficiary))}" disabled></div>
        </div>
      </div>
      <div class="portal-panel">
        <form method="POST">
          <div class="grid grid-1">
            <div><label>كلمة المرور الحالية</label><input type="password" name="current_password" required></div>
            <div><label>كلمة المرور الجديدة</label><input type="password" name="new_password" required></div>
          </div>
          <div class="actions" style="margin-top:16px"><button class="btn btn-primary" type="submit">تحديث كلمة المرور</button></div>
        </form>
      </div>
    </div>
    """
    return render_user_page("ملفي الشخصي", content)


def _clean_user_register():
    if request.method == "POST":
        flash("\u062a\u0645 \u0627\u0633\u062a\u0644\u0627\u0645 \u0637\u0644\u0628 \u0627\u0644\u0627\u0634\u062a\u0631\u0627\u0643 \u062f\u0627\u062e\u0644\u064a\u064b\u0627. \u0633\u062a\u0642\u0648\u0645 \u0627\u0644\u0625\u062f\u0627\u0631\u0629 \u0628\u0645\u0631\u0627\u062c\u0639\u0629 \u0627\u0644\u0628\u064a\u0627\u0646\u0627\u062a \u0648\u062a\u062c\u0647\u064a\u0632 \u0627\u0644\u062d\u0633\u0627\u0628 \u0627\u0644\u0645\u0646\u0627\u0633\u0628 \u0639\u0646\u062f \u0627\u0644\u0627\u0639\u062a\u0645\u0627\u062f.", "info")
        return redirect(url_for("user_register"))
    content = """
    <section class="portal-auth-hero">
      <div>
        <span class="badge badge-blue">بوابة المشتركين</span>
        <h1>تسجيل اشتراك جديد</h1>
        <p>سجل بياناتك الأساسية ليتم التواصل معك وتجهيز الحساب المناسب لك، سواء كان حساب يوزر إنترنت أو بطاقات أسبوعية.</p>
      </div>
      <div class="portal-feature-list">
        <div><i class="fa-solid fa-user-check"></i><span>حساب بوابة للمشترك</span></div>
        <div><i class="fa-solid fa-wifi"></i><span>خدمات إنترنت بالمراجعة الإدارية</span></div>
        <div><i class="fa-solid fa-credit-card"></i><span>بطاقات بحدود أسبوعية للمؤهلين</span></div>
      </div>
    </section>
    <div class="portal-panel">
      <form method="POST">
        <div class="grid grid-2">
          <div><label>الاسم الكامل</label><input name="full_name" placeholder="الاسم الرباعي" required></div>
          <div><label>رقم الجوال</label><input name="phone" placeholder="05xxxxxxxx" required></div>
          <div><label>نوع الاستفادة المطلوبة</label><select name="access_mode"><option value="username">يوزر إنترنت</option><option value="cards">بطاقات استخدام</option></select></div>
          <div><label>جهة الاستفادة</label><input name="study_or_work" placeholder="دراسة، عمل حر، جامعة..."></div>
          <div class="grid-col-span-2"><label>ملاحظات</label><textarea name="notes" class="notes-box" placeholder="أي بيانات تساعد الإدارة على تجهيز الحساب المناسب"></textarea></div>
        </div>
        <div class="actions" style="margin-top:16px">
          <button class="btn btn-primary" type="submit">إرسال طلب الاشتراك</button>
          <a class="btn btn-soft" href="/user/login">لديك حساب؟ تسجيل الدخول</a>
        </div>
      </form>
    </div>
    """
    return render_user_page("تسجيل اشتراك", content)
