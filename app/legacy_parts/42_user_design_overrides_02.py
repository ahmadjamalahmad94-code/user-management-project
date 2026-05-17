# Continued split from 42_user_design_overrides.py lines 136-282. Loaded by app.legacy.


def _designed_user_internet_access_page():
    beneficiary = get_current_portal_beneficiary()
    access_mode = get_beneficiary_access_mode(beneficiary)
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
    if access_mode == "cards":
        content = f"""
        <section class="portal-hero-card compact">
          <div>
            <span class="badge badge-blue">بطاقات استخدام</span>
            <h1>البطاقات والحالة</h1>
            <p>تعرض هذه الصفحة ملخص حالتك وتجدد الحدود الأسبوعية كل جمعة.</p>
          </div>
        </section>
        {f"<div class='flash warning'>{safe(error_text)}</div>" if error_text else ""}
        <div class="summary-grid">
          <div class="summary-card"><div class="label">المشترك</div><div class="value" style="font-size:18px">{safe(beneficiary.get('full_name'))}</div></div>
          <div class="summary-card"><div class="label">حالة الربط</div><div class="value" style="font-size:18px">{internet_request_status_pill(account.get('status') or 'pending')}</div></div>
          <div class="summary-card"><div class="label">أقرب تجديد</div><div class="value" style="font-size:18px">{portal_next_friday_date().strftime('%Y-%m-%d')}</div></div>
        </div>
        <div class="portal-panel" style="margin-top:16px">
          <div class="section-heading"><div><h3>معلومات الاستخدام</h3><p>يتم إظهار ما هو متاح من بيانات البطاقات لحسابك.</p></div></div>
          {("<pre>" + safe(json.dumps(cards_data, ensure_ascii=False, indent=2)) + "</pre>") if cards_data else "<div class='empty-state-card'>لم يتم إصدار بطاقات بعد أو لا توجد بيانات متاحة حاليًا.</div>"}
        </div>
        """
        return render_user_page("البطاقات والحالة", content)
    content = f"""
    <section class="portal-hero-card compact">
      <div>
        <span class="badge badge-blue">حساب اليوزر</span>
        <h1>حساب الإنترنت</h1>
        <p>ملخص لحسابك المرتبط مع بيانات البروفايل والاستهلاك والجلسات عندما تكون متاحة.</p>
      </div>
    </section>
    {f"<div class='flash warning'>{safe(error_text)}</div>" if error_text else ""}
    <div class="summary-grid">
      <div class="summary-card"><div class="label">اسم المستخدم الخارجي</div><div class="value" style="font-size:18px">{safe(account.get('external_username')) or '-'}</div></div>
      <div class="summary-card"><div class="label">الحالة</div><div class="value" style="font-size:18px">{internet_request_status_pill(account.get('status') or 'pending')}</div></div>
      <div class="summary-card"><div class="label">البروفايل</div><div class="value" style="font-size:18px">{safe(account.get('current_profile_name')) or safe(account.get('current_profile_id')) or '-'}</div></div>
    </div>
    <div class="grid grid-2" style="margin-top:16px">
      <div class="portal-panel"><div class="section-heading"><div><h3>الاستهلاك</h3><p>مختصر الاستخدام المتاح.</p></div></div>{("<pre>" + safe(json.dumps(usage_data, ensure_ascii=False, indent=2)) + "</pre>") if usage_data else "<div class='empty-state-card'>لا توجد بيانات استهلاك متاحة حاليًا.</div>"}</div>
      <div class="portal-panel"><div class="section-heading"><div><h3>الجلسات والبطاقات</h3><p>ما هو متاح عن جلساتك والبطاقات المرتبطة.</p></div></div>{("<pre>" + safe(json.dumps({'sessions': sessions_data, 'cards': cards_data}, ensure_ascii=False, indent=2)) + "</pre>") if sessions_data or cards_data else "<div class='empty-state-card'>لا توجد جلسات أو بطاقات معروضة حاليًا.</div>"}</div>
    </div>
    """
    return render_user_page("حساب الإنترنت", content)


def _designed_render_user_request_form():
    beneficiary = get_current_portal_beneficiary()
    access_mode = get_beneficiary_access_mode(beneficiary)
    workday = portal_workday_context()
    if access_mode == "cards":
        content = f"""
        <section class="portal-hero-card compact">
          <div>
            <span class="badge badge-blue">طلب بطاقة</span>
            <h1>طلب بطاقة استخدام</h1>
            <p>سيتم تقييم الطلب حسب الوقت المتبقي للدوام والحدود الأسبوعية. التجديد كل جمعة.</p>
          </div>
        </section>
        <div class="portal-panel">
          <div class="info-note">الوقت المتبقي حتى الرابعة: <strong>{workday['remaining_minutes']} دقيقة</strong></div>
          <form method="POST" style="margin-top:16px">
            <input type="hidden" name="request_type" value="request_card">
            <input type="hidden" name="card_count" value="1">
            <input type="hidden" id="portal-duration" name="duration_minutes" value="60">
            <div class="section-heading"><div><h3>اختر نوع البطاقة</h3><p>يظهر التقييم الأولي حسب الوقت المتبقي للدوام.</p></div></div>
            {portal_card_options_html()}
            <div class="grid grid-2" style="margin-top:16px">
              <div><label>ملاحظة للإدارة</label><textarea name="notes" class="notes-box" placeholder="اكتب السبب أو الاستخدام المطلوب"></textarea></div>
              <div class="portal-side-note">
                <h4>توجيه سريع</h4>
                <p>إذا كان الوقت المتبقي قصيرًا، فستكون البطاقات الأقصر أولى بالاعتماد. الإدارة تحافظ على عدالة التوزيع طوال الأسبوع.</p>
              </div>
            </div>
            <div class="actions" style="margin-top:16px">
              <button class="btn btn-primary" type="submit">إرسال طلب البطاقة</button>
              <a class="btn btn-soft" href="{url_for('user_internet_my_requests_page')}">طلباتي</a>
            </div>
          </form>
        </div>
        """
        return render_user_page("طلب بطاقة", content)
    content = f"""
    <section class="portal-hero-card compact">
      <div>
        <span class="badge badge-blue">طلب خدمة</span>
        <h1>طلب خدمة لليوزر</h1>
        <p>اختر الخدمة المرتبطة بحساب الإنترنت الخاص بك، وستصل للإدارة للمراجعة والتنفيذ.</p>
      </div>
    </section>
    <div class="portal-panel">
      <div class="small" style="margin-bottom:12px">المستفيد الحالي: {safe(beneficiary.get('full_name'))} - {safe(beneficiary.get('phone'))}</div>
      <form method="POST">
        <div class="grid grid-2">
          <div><label>نوع الطلب</label><select name="request_type" required>
            <option value="create_user">إنشاء حساب إنترنت</option>
            <option value="temporary_speed_upgrade">رفع سرعة مؤقت</option>
            <option value="add_time">إضافة وقت</option>
            <option value="add_quota">إضافة كوتة</option>
            <option value="update_mac">تحديث MAC</option>
            <option value="reset_password">إعادة تعيين كلمة المرور</option>
          </select></div>
          <div><label>اسم المستخدم الخارجي</label><input name="external_username"></div>
          <div><label>اسم مستخدم جديد</label><input name="desired_username"></div>
          <div><label>رقم / اسم البروفايل</label><div class="grid grid-2"><input name="profile_id" placeholder="profile_id"><input name="profile_name" placeholder="profile_name"></div></div>
          <div><label>مدة رفع السرعة بالدقائق</label><input name="duration_minutes" type="number" min="1" value="60"></div>
          <div><label>إضافة وقت</label><div class="grid grid-2"><input name="time_amount" type="number" min="1"><select name="time_unit"><option value="minutes">دقائق</option><option value="hours">ساعات</option><option value="days">أيام</option></select></div></div>
          <div><label>إضافة كوتة</label><div class="grid grid-3"><input name="quota_amount_mb" type="number" min="1" placeholder="إجمالي"><input name="upload_quota_mb" type="number" min="0" placeholder="رفع"><input name="download_quota_mb" type="number" min="0" placeholder="تنزيل"></div></div>
          <div><label>عنوان MAC</label><input name="mac_address" placeholder="AA:BB:CC:DD:EE:FF"></div>
          <div class="grid-col-span-2"><label>ملاحظات</label><textarea name="notes" class="notes-box" placeholder="تفاصيل إضافية للإدارة"></textarea></div>
        </div>
        <div class="actions" style="margin-top:16px">
          <button class="btn btn-primary" type="submit">إرسال الطلب</button>
        </div>
      </form>
    </div>
    """
    return render_user_page("طلب خدمة", content)


def _designed_user_internet_request_page():
    beneficiary = get_current_portal_beneficiary()
    if request.method == "POST":
        _beneficiary_id, request_type, requested_payload = normalize_internet_request_form(request.form)
        requested_payload["portal_source"] = "beneficiary"
        requested_payload["portal_access_mode"] = get_beneficiary_access_mode(beneficiary)
        req_id = create_internet_service_request(beneficiary["id"], request_type, requested_payload)
        log_action("submit_internet_request_user", "internet_request", req_id, f"User submitted {request_type} for beneficiary {beneficiary['id']}")
        flash("تم إرسال الطلب وهو الآن قيد المراجعة.", "success")
        return redirect(url_for("user_internet_my_requests_page"))
    return _designed_render_user_request_form()
