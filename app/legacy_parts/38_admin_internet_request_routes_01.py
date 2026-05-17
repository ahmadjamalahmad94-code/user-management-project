# Auto-split from app/legacy.py lines 7999-8304. Loaded by app.legacy.
@app.route("/internet/my-requests")
@login_required
@permission_required("view_internet_requests")
def internet_my_requests_page():
    rows = query_all(
        """
        SELECT r.*, b.full_name
        FROM internet_service_requests r
        JOIN beneficiaries b ON b.id = r.beneficiary_id
        WHERE r.requested_by=%s
        ORDER BY r.id DESC
        """,
        [session.get("username", "")],
    )
    items = ""
    for row in rows:
        details_link = (
            f"<a class='btn btn-soft btn-icon' href='{url_for('admin_internet_request_detail_page', request_id=row['id'])}' title='عرض'><i class='fa-solid fa-eye'></i></a>"
            if has_permission("manage_internet_requests")
            else "-"
        )
        items += f"""
        <tr>
          <td>{row['id']}</td>
          <td>{safe(row.get('full_name'))}</td>
          <td>{safe(internet_request_type_label(row.get('request_type')))}</td>
          <td>{internet_request_status_pill(row.get('status'))}</td>
          <td class='cell-wrap'>{request_payload_summary(json_safe_dict(row.get('requested_payload')))}</td>
          <td>{format_dt_short(row.get('created_at'))}</td>
          <td>{details_link}</td>
        </tr>
        """
    content = f"""
    <div class='hero'>
      <div><h1>طلباتي</h1><p>هذه الصفحة تعرض الطلبات المسجلة بواسطة الحساب الحالي داخل Hobe Hub.</p></div>
      <div class='actions'><a class='btn btn-primary' href='{url_for("internet_request_page")}'>طلب جديد</a></div>
    </div>
    <div class='table-wrap'>
      <table>
        <thead><tr><th>#</th><th>المستفيد</th><th>النوع</th><th>الحالة</th><th>البيانات</th><th>تاريخ الطلب</th><th>تفاصيل</th></tr></thead>
        <tbody>{items or "<tr><td colspan='7'>لا توجد طلبات حتى الآن.</td></tr>"}</tbody>
      </table>
    </div>
    """
    return render_page("طلباتي", content)


@app.route("/internet/my-access")
@login_required
@permission_required("view_internet_requests")
def internet_my_access_page():
    beneficiary_id = int(clean_csv_value(request.args.get("beneficiary_id", "0")) or "0")
    beneficiaries = query_all("SELECT id, full_name FROM beneficiaries ORDER BY id DESC LIMIT 500")
    options = "".join(
        f"<option value='{r['id']}' {'selected' if beneficiary_id == r['id'] else ''}>{safe(r.get('full_name'))}</option>"
        for r in beneficiaries
    )
    access_html = "<div class='card'>اختر مستفيدًا لعرض الربط الخارجي.</div>"
    if beneficiary_id > 0:
        account = get_radius_account(beneficiary_id) or {}
        remote_sections = ""
        username = clean_csv_value(account.get("external_username"))
        if username:
            try:
                client = get_radius_client()
                usage = mask_sensitive_data(client.get_user_usage({"username": username}))
                bandwidth = mask_sensitive_data(client.get_user_bandwidth({"username": username}))
                remote_sections = f"""
                <div class='grid grid-2' style='margin-top:16px'>
                  <div class='card'><h3>الاستهلاك</h3><pre>{safe(json.dumps(usage, ensure_ascii=False, indent=2))}</pre></div>
                  <div class='card'><h3>الحالة الحالية</h3><pre>{safe(json.dumps(bandwidth, ensure_ascii=False, indent=2))}</pre></div>
                </div>
                """
            except Exception as exc:
                remote_sections = f"<div class='flash warning'>تعذر جلب الملخص الخارجي الآن: {safe(str(exc))}</div>"
        access_html = f"""
        <div class='card'>
          <div class='grid grid-2'>
            <div><label>اسم المستخدم الخارجي</label><div class='badge'>{safe(account.get('external_username')) or '-'}</div></div>
            <div><label>الحالة</label><div>{internet_request_status_pill(account.get('status') or 'pending')}</div></div>
            <div><label>البروفايل الحالي</label><div>{safe(account.get('current_profile_name')) or safe(account.get('current_profile_id')) or '-'}</div></div>
            <div><label>البروفايل الأصلي</label><div>{safe(account.get('original_profile_id')) or '-'}</div></div>
          </div>
        </div>
        {remote_sections}
        """
    content = f"""
    <div class='hero'>
      <div><h1>الوصول المرتبط</h1><p>عرض الربط المحلي مع حساب RADIUS وملخص الاستخدام الخارجي إن توفر.</p></div>
    </div>
    <div class='card'>
      <form method='GET'>
        <div class='grid grid-2'>
          <div><label>المستفيد</label><select name='beneficiary_id'>{options}</select></div>
          <div class='actions' style='align-items:end'><button class='btn btn-primary' type='submit'>عرض البيانات</button></div>
        </div>
      </form>
    </div>
    <div style='margin-top:16px'>{access_html}</div>
    """
    return render_page("الوصول المرتبط", content)
