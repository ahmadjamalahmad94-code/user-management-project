# Continued split from 36_user_internet_routes.py lines 143-227. Loaded by app.legacy.


@app.route("/user/internet")
@user_login_required
def user_internet_access_page():
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
    content = f"""
    <div class="hero"><div><h1>حساب الإنترنت</h1><p>عرض الربط الخاص بك فقط مع ملخص الاستخدام والجلسات إن كانت الخدمة متاحة.</p></div></div>
    {f"<div class='flash warning'>{safe(error_text)}</div>" if error_text else ""}
    <div class="card">
      <div class="grid grid-2">
        <div><label>المستفيد</label><div>{safe(beneficiary.get('full_name'))}</div></div>
        <div><label>اسم المستخدم الخارجي</label><div>{safe(account.get('external_username')) or '-'}</div></div>
        <div><label>الحالة</label><div>{internet_request_status_pill(account.get('status') or 'pending')}</div></div>
        <div><label>البروفايل الحالي</label><div>{safe(account.get('current_profile_name')) or safe(account.get('current_profile_id')) or '-'}</div></div>
      </div>
    </div>
    <div class="grid grid-2" style="margin-top:16px">
      <div class="card"><h3>الاستهلاك</h3><pre>{safe(json.dumps(usage_data, ensure_ascii=False, indent=2)) if usage_data else '-'}</pre></div>
      <div class="card"><h3>الجلسات والبطاقات</h3><pre>{safe(json.dumps({'sessions': sessions_data, 'cards': cards_data}, ensure_ascii=False, indent=2)) if sessions_data or cards_data else '-'}</pre></div>
    </div>
    """
    return render_user_page("حساب الإنترنت", content)


@app.route("/user/internet/request", methods=["GET", "POST"])
@user_login_required
def user_internet_request_page():
    beneficiary = get_current_portal_beneficiary()
    if request.method == "POST":
        _beneficiary_id, request_type, requested_payload = normalize_internet_request_form(request.form)
        requested_payload["portal_source"] = "beneficiary"
        req_id = create_internet_service_request(beneficiary["id"], request_type, requested_payload)
        log_action("submit_internet_request_user", "internet_request", req_id, f"User submitted {request_type} for beneficiary {beneficiary['id']}")
        flash("تم إرسال الطلب وهو الآن قيد المراجعة.", "success")
        return redirect(url_for("user_internet_my_requests_page"))
    return render_user_request_form()


@app.route("/user/internet/my-requests")
@user_login_required
def user_internet_my_requests_page():
    rows = get_user_requests()
    items = ""
    for row in rows:
        items += f"""
        <tr>
          <td>{row['id']}</td>
          <td>{safe(internet_request_type_label(row.get('request_type')))}</td>
          <td>{internet_request_status_pill(row.get('status'))}</td>
          <td class='cell-wrap'>{request_payload_summary(json_safe_dict(row.get('requested_payload')))}</td>
          <td>{safe(row.get('error_message')) or '-'}</td>
          <td>{format_dt_short(row.get('created_at'))}</td>
        </tr>
        """
    content = f"""
    <div class="hero"><div><h1>طلباتي</h1><p>هذه القائمة تعرض طلباتك فقط، ولا يمكن من خلالها اعتماد أو تنفيذ أي إجراء.</p></div></div>
    <div class="table-wrap">
      <table>
        <thead><tr><th>#</th><th>النوع</th><th>الحالة</th><th>البيانات</th><th>ملاحظة</th><th>التاريخ</th></tr></thead>
        <tbody>{items or "<tr><td colspan='6'>لا توجد طلبات حتى الآن.</td></tr>"}</tbody>
      </table>
    </div>
    """
    return render_user_page("طلباتي", content)


@app.route("/user/internet/my-access")
@user_login_required
def user_internet_my_access_page():
    return user_internet_access_page()
