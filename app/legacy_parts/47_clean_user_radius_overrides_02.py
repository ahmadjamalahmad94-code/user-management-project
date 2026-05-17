# Continued split from 47_clean_user_radius_overrides.py lines 134-274. Loaded by app.legacy.


def _clean_user_internet_request_page():
    beneficiary = get_current_portal_beneficiary()
    if request.method == "POST":
        _beneficiary_id, request_type, requested_payload = normalize_internet_request_form(request.form)
        requested_payload["portal_source"] = "beneficiary"
        requested_payload["portal_access_mode"] = get_beneficiary_access_mode(beneficiary)
        req_id = create_internet_service_request(beneficiary["id"], request_type, requested_payload)
        log_action("submit_internet_request_user", "internet_request", req_id, f"User submitted {request_type} for beneficiary {beneficiary['id']}")
        flash("تم إرسال الطلب وهو الآن قيد المراجعة.", "success")
        return redirect(url_for("user_internet_my_requests_page"))
    content = f"""
    <section class="portal-hero-card compact">
      <div>
        <span class="badge badge-blue">طلب خدمة</span>
        <h1>تقديم طلب جديد</h1>
        <p>اختر الخدمة المناسبة لحساب الإنترنت الخاص بك، وسيقوم فريق الإدارة بمراجعتها وتنفيذها عند الاعتماد.</p>
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
          <div><label>رقم أو اسم الملف</label><div class="grid grid-2"><input name="profile_id" placeholder="profile_id"><input name="profile_name" placeholder="profile_name"></div></div>
          <div><label>مدة رفع السرعة بالدقائق</label><input name="duration_minutes" type="number" min="1" value="60"></div>
          <div><label>إضافة وقت</label><div class="grid grid-2"><input name="time_amount" type="number" min="1"><select name="time_unit"><option value="minutes">دقائق</option><option value="hours">ساعات</option><option value="days">أيام</option></select></div></div>
          <div><label>إضافة كوتة</label><div class="grid grid-3"><input name="quota_amount_mb" type="number" min="1" placeholder="إجمالي"><input name="upload_quota_mb" type="number" min="0" placeholder="رفع"><input name="download_quota_mb" type="number" min="0" placeholder="تنزيل"></div></div>
          <div><label>عنوان MAC</label><input name="mac_address" placeholder="AA:BB:CC:DD:EE:FF"></div>
          <div class="grid-col-span-2"><label>ملاحظات</label><textarea name="notes" class="notes-box" placeholder="أي تفاصيل إضافية تساعد الإدارة على تنفيذ الطلب"></textarea></div>
        </div>
        <div class="actions" style="margin-top:16px">
          <button class="btn btn-primary" type="submit">إرسال الطلب</button>
        </div>
      </form>
    </div>
    """
    return render_user_page("طلب خدمة", content)


def _clean_user_internet_my_requests_page():
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
            <div><label>التفاصيل</label><div>{request_payload_summary(payload)}</div></div>
            <div><label>ملاحظات التنفيذ</label><div>{safe(row.get('error_message')) or '-'}</div></div>
          </div>
        </article>
        """
    content = f"""
    <section class="portal-hero-card compact">
      <div>
        <span class="badge badge-blue">طلباتي</span>
        <h1>متابعة حالة الطلبات</h1>
        <p>تجد هنا تسلسل الطلبات من قيد المراجعة وحتى التنفيذ أو الرفض بشكل واضح ومباشر.</p>
      </div>
    </section>
    <div class="summary-grid" style="margin-bottom:16px">
      <div class="summary-card"><div class="label">إجمالي الطلبات</div><div class="value">{len(rows)}</div></div>
      <div class="summary-card"><div class="label">قيد المراجعة</div><div class="value">{len([r for r in rows if r.get('status') == 'pending'])}</div></div>
      <div class="summary-card"><div class="label">تم التنفيذ</div><div class="value">{len([r for r in rows if r.get('status') == 'executed'])}</div></div>
    </div>
    {cards or "<div class='empty-state-card'>لا توجد طلبات حاليًا. يمكنك البدء من صفحة طلب الخدمة.</div>"}
    """
    return render_user_page("طلباتي", content)


def _clean_user_profile_page():
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
        flash("تم تحديث كلمة المرور بنجاح.", "success")
        return redirect(url_for("user_profile_page"))
    content = f"""
    <section class="portal-hero-card compact">
      <div>
        <span class="badge badge-blue">ملفي الشخصي</span>
        <h1>بيانات الحساب</h1>
        <p>راجع بياناتك الأساسية وحدّث كلمة المرور الخاصة ببوابة المشترك من هنا.</p>
      </div>
    </section>
    <div class="grid grid-2">
      <div class="portal-panel">
        <div class="grid grid-2">
          <div><label>الاسم</label><input value="{safe(beneficiary.get('full_name'))}" disabled></div>
          <div><label>رقم الجوال</label><input value="{safe(beneficiary.get('phone')) or '-'}" disabled></div>
          <div><label>اسم المستخدم</label><input value="{safe(session.get('beneficiary_username'))}" disabled></div>
          <div><label>نوع الخدمة</label><input value="{safe(get_beneficiary_access_label(beneficiary))}" disabled></div>
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
