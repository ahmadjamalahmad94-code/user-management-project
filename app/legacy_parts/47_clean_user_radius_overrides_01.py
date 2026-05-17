# Auto-split from app/legacy.py lines 10413-10879. Loaded by app.legacy.
USER_BASE_TEMPLATE = _legacy_template_text('47_clean_user_radius_overrides.USER_BASE_TEMPLATE.html')


def render_user_page(title, content):
    beneficiary = get_current_portal_beneficiary() if session.get("portal_type") == "beneficiary" else None
    access_mode = get_beneficiary_access_mode(beneficiary)
    return render_template_string(
        USER_BASE_TEMPLATE,
        title=title,
        content=content,
        portal_access_mode=access_mode,
        portal_access_label=get_beneficiary_access_label(beneficiary),
        portal_copy=_clean_portal_access_type_copy(access_mode),
        hebron_now=portal_now_hebron(),
    )


def _clean_user_dashboard():
    beneficiary = get_current_portal_beneficiary()
    radius_account = get_user_radius_account() or {}
    requests_rows = get_user_requests()
    access_mode = get_beneficiary_access_mode(beneficiary)
    pending_count = len([r for r in requests_rows if r.get("status") == "pending"])
    executed_count = len([r for r in requests_rows if r.get("status") == "executed"])
    latest_request = requests_rows[0] if requests_rows else None
    if access_mode == "cards":
        latest_card = get_latest_issued_card_for_beneficiary(beneficiary["id"])
        content = f"""
        <section class="portal-hero-card">
          <div>
            <span class="badge badge-blue">بوابة البطاقات</span>
            <h1>مرحبًا {safe(beneficiary.get('full_name'))}</h1>
            <p>هنا تتابع طلبات البطاقات والحدود الأسبوعية وآخر بطاقة تم إصدارها لك بشكل واضح وسريع.</p>
          </div>
          <div class="summary-grid">
            <div class="summary-card"><div class="label">طلبات اليوم</div><div class="value">{count_beneficiary_card_requests_today(beneficiary['id'])}</div></div>
            <div class="summary-card"><div class="label">طلبات الأسبوع</div><div class="value">{count_beneficiary_card_requests_week(beneficiary['id'])}</div></div>
            <div class="summary-card"><div class="label">التجديد الأسبوعي</div><div class="value">{portal_next_friday_date().strftime('%Y-%m-%d')}</div></div>
          </div>
        </section>
        <div class="grid grid-2" style="margin-top:18px">
          <div class="portal-panel">
            <div class="section-heading"><div><h3>آخر بطاقة</h3><p>آخر بطاقة صادرة لك مع حالة الاستخدام الحالية.</p></div></div>
            <div class="summary-grid">
              <div class="summary-card"><div class="label">اسم المستخدم</div><div class="value" style="font-size:18px">{safe((latest_card or {}).get('card_username')) or '-'}</div></div>
              <div class="summary-card"><div class="label">المدة</div><div class="value" style="font-size:18px">{safe((latest_card or {}).get('duration_label')) or '-'}</div></div>
              <div class="summary-card"><div class="label">حالة آخر طلب</div><div class="value" style="font-size:18px">{internet_request_status_pill((latest_request or {}).get('status') or 'pending')}</div></div>
            </div>
          </div>
          <div class="portal-panel">
            <div class="section-heading"><div><h3>اختصارات سريعة</h3><p>انتقل مباشرة إلى البطاقة أو الطلبات أو الملف الشخصي.</p></div></div>
            <div class="request-actions">
              <a class="btn btn-primary" href="{url_for('user_internet_request_page')}">طلب بطاقة</a>
              <a class="btn btn-soft" href="{url_for('user_internet_access_page')}">البطاقات والحالة</a>
              <a class="btn btn-soft" href="{url_for('user_internet_my_requests_page')}">طلباتي</a>
            </div>
          </div>
        </div>
        """
        return render_user_page("الرئيسية", content)
    content = f"""
    <section class="portal-hero-card">
      <div>
        <span class="badge badge-blue">حساب إنترنت</span>
        <h1>مرحبًا {safe(beneficiary.get('full_name'))}</h1>
        <p>هذه الصفحة تعرض ملخص حساب الإنترنت المرتبط بك وطلباتك الحالية بشكل مبسط وواضح.</p>
      </div>
      <div class="summary-grid">
        <div class="summary-card"><div class="label">اسم المستخدم</div><div class="value" style="font-size:18px">{safe(radius_account.get('external_username')) or '-'}</div></div>
        <div class="summary-card"><div class="label">الملف الحالي</div><div class="value" style="font-size:18px">{safe(radius_account.get('current_profile_name')) or safe(radius_account.get('current_profile_id')) or '-'}</div></div>
        <div class="summary-card"><div class="label">طلبات قيد المراجعة</div><div class="value">{pending_count}</div></div>
      </div>
    </section>
    <div class="grid grid-2" style="margin-top:18px">
      <div class="portal-panel">
        <div class="section-heading"><div><h3>متابعة الحساب</h3><p>راجع حالة الربط وملف الإنترنت الحالي وبيانات الاستخدام إن كانت متاحة.</p></div></div>
        <div class="summary-grid">
          <div class="summary-card"><div class="label">حالة الربط</div><div class="value" style="font-size:18px">{internet_request_status_pill(radius_account.get('status') or 'pending')}</div></div>
          <div class="summary-card"><div class="label">طلبات منفذة</div><div class="value">{executed_count}</div></div>
        </div>
      </div>
      <div class="portal-panel">
        <div class="section-heading"><div><h3>اختصارات سريعة</h3><p>للوصول السريع إلى الحساب والخدمات والطلبات.</p></div></div>
        <div class="request-actions">
          <a class="btn btn-primary" href="{url_for('user_internet_access_page')}">حساب الإنترنت</a>
          <a class="btn btn-soft" href="{url_for('user_internet_request_page')}">طلب خدمة</a>
          <a class="btn btn-soft" href="{url_for('user_internet_my_requests_page')}">طلباتي</a>
        </div>
      </div>
    </div>
    """
    return render_user_page("الرئيسية", content)


def _clean_user_internet_access_page():
    beneficiary = get_current_portal_beneficiary()
    account = get_user_radius_account() or {}
    username = clean_csv_value(account.get("external_username"))
    usage_data = {}
    sessions_data = {}
    cards_data = {}
    error_text = ""
    if username:
        try:
            client = get_radius_client()
            usage_data = mask_sensitive_data(client.get_user_usage({"username": username}))
            sessions_data = mask_sensitive_data(client.get_user_sessions({"username": username}))
            cards_data = mask_sensitive_data(client.get_user_cards({"username": username}))
        except Exception as exc:
            error_text = str(exc)
    details_html = f"<pre>{safe(json.dumps(usage_data, ensure_ascii=False, indent=2))}</pre>" if usage_data else "<div class='empty-state-card'>لا توجد بيانات استخدام متاحة حاليًا.</div>"
    sessions_html = f"<pre>{safe(json.dumps({'sessions': sessions_data, 'cards': cards_data}, ensure_ascii=False, indent=2))}</pre>" if sessions_data or cards_data else "<div class='empty-state-card'>لا توجد جلسات أو بطاقات مرتبطة معروضة حاليًا.</div>"
    content = f"""
    <section class="portal-hero-card compact">
      <div>
        <span class="badge badge-blue">حساب الإنترنت</span>
        <h1>متابعة الحساب والاتصال</h1>
        <p>راجع حالة الحساب المرتبط بك وبيانات الاستخدام والجلسات عندما تكون متاحة من المصدر الخارجي.</p>
      </div>
    </section>
    {f"<div class='flash warning'>{safe(error_text)}</div>" if error_text else ""}
    <div class="summary-grid">
      <div class="summary-card"><div class="label">اسم المستخدم</div><div class="value" style="font-size:18px">{safe(account.get('external_username')) or '-'}</div></div>
      <div class="summary-card"><div class="label">الحالة</div><div class="value" style="font-size:18px">{internet_request_status_pill(account.get('status') or 'pending')}</div></div>
      <div class="summary-card"><div class="label">الملف الحالي</div><div class="value" style="font-size:18px">{safe(account.get('current_profile_name')) or safe(account.get('current_profile_id')) or '-'}</div></div>
    </div>
    <div class="grid grid-2" style="margin-top:16px">
      <div class="portal-panel"><div class="section-heading"><div><h3>الاستخدام</h3><p>الملخص المتاح من الخدمة الخارجية.</p></div></div>{details_html}</div>
      <div class="portal-panel"><div class="section-heading"><div><h3>الجلسات والبطاقات</h3><p>أي جلسات أو بطاقات مرتبطة تظهر هنا إن وجدت.</p></div></div>{sessions_html}</div>
    </div>
    """
    return render_user_page("حساب الإنترنت", content)
