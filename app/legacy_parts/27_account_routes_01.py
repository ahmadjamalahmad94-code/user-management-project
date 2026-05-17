# Auto-split from app/legacy.py lines 5493-5735. Loaded by app.legacy.
@app.route("/accounts")
@login_required
@permission_required("manage_accounts")
def accounts_page():
    rows = query_all("""
        SELECT a.*,
               COALESCE(string_agg(p.name, ', ' ORDER BY p.name), '') AS perms
        FROM app_accounts a
        LEFT JOIN account_permissions ap ON ap.account_id = a.id
        LEFT JOIN permissions p ON p.id = ap.permission_id
        GROUP BY a.id
        ORDER BY a.id DESC
    """)
    table_rows = ""
    for r in rows:
        perms = [x.strip() for x in safe(r['perms']).split(',') if x.strip()]
        perms_html = "<div class='permission-chip-wrap'>" + ("".join([f"<span class='permission-chip'><i class='fa-solid fa-shield-halved'></i> {permission_label(p)}</span>" for p in perms]) if perms else "<span class='small'>لا توجد صلاحيات محددة</span>") + "</div>"
        status_badge = "<span class='badge badge-green'>مفعل</span>" if r['is_active'] else "<span class='badge badge-orange'>معطل</span>"
        table_rows += f"""
        <tr>
          <td>{r['id']}</td>
          <td><strong>{safe(r['username'])}</strong></td>
          <td>{safe(r['full_name']) or '-'}</td>
          <td>{status_badge}</td>
          <td style='max-width:420px;white-space:normal'>{perms_html}</td>
          <td>
            <div class='actions' style='justify-content:center'>
              <a class="btn btn-secondary btn-icon" href="/accounts/edit/{r['id']}" title="تعديل"><i class="fa-solid fa-pen"></i></a>
              <form class="inline-form" method="POST" action="/accounts/toggle/{r['id']}"><button class="btn btn-outline btn-icon" type="submit" title="تفعيل أو تعطيل"><i class="fa-solid fa-power-off"></i></button></form>
            </div>
          </td>
        </tr>
        """
    html = f"""
    <div class="hero"><h1>إدارة المستخدمين والصلاحيات</h1><p>واجهة أكثر وضوحًا لتوزيع الصلاحيات، مع بطاقات ملوّنة وسهلة المراجعة لكل مستخدم.</p></div>
    <div class="card glass-card toolbar-card">
      <div>
        <strong>إجمالي الحسابات:</strong> {len(rows)}
        <div class="small" style="margin-top:4px">أنشئ مستخدمين بصلاحيات دقيقة للسجل، الأرشيف، التصدير، والاسترجاع.</div>
      </div>
      <div class="actions"><a class="btn btn-primary" href="/accounts/add"><i class="fa-solid fa-user-plus"></i> إضافة مستخدم</a></div>
    </div>
    <div class="card" style="margin-top:16px">
      <div class="table-wrap">
        <table>
          <thead><tr><th>#</th><th>اسم المستخدم</th><th>الاسم الكامل</th><th>الحالة</th><th>الصلاحيات</th><th>إجراءات</th></tr></thead>
          <tbody>{table_rows or "<tr><td colspan='6' class='empty-state'>لا توجد حسابات بعد.</td></tr>"}</tbody>
        </table>
      </div>
    </div>
    """
    return render_page("إدارة المستخدمين", html)


def permissions_checkboxes(selected=None):
    selected = set(selected or [])
    html = "<div class='permissions-grid'>"
    for p in PERMISSIONS:
        checked = "checked" if p in selected else ""
        active_cls = " checked" if p in selected else ""
        html += f"""
        <label class='permission-card{active_cls}'>
          <input type='checkbox' name='permissions' value='{p}' {checked} onchange="this.closest('.permission-card').classList.toggle('checked', this.checked)">
          <div>
            <div class='permission-card-title'>{permission_label(p)}</div>
            <div class='permission-card-desc'>{safe(PERMISSION_DESCRIPTIONS.get(p, ''))}</div>
          </div>
        </label>
        """
    html += "</div>"
    return html


@app.route("/accounts/add", methods=["GET", "POST"])
@login_required
@permission_required("manage_accounts")
def add_account():
    if request.method == "POST":
        username = clean_csv_value(request.form.get("username"))
        password = clean_csv_value(request.form.get("password"))
        full_name = clean_csv_value(request.form.get("full_name"))
        perms = request.form.getlist("permissions")
        if not username or not password:
            flash("اسم المستخدم وكلمة المرور مطلوبان.", "error")
            return redirect(url_for("add_account"))
        try:
            row = execute_sql("""
                INSERT INTO app_accounts (username, password_hash, full_name, is_active)
                VALUES (%s,%s,%s,TRUE)
                RETURNING id
            """, [username, admin_password_hash(password), full_name], fetchone=True)
        except psycopg2.Error:
            flash("اسم المستخدم مستخدم مسبقًا أو يوجد خطأ في قاعدة البيانات.", "error")
            return redirect(url_for("add_account"))
        aid = row["id"]
        for p in perms:
            execute_sql("""
                INSERT INTO account_permissions (account_id, permission_id)
                SELECT %s, id FROM permissions WHERE name=%s
                ON CONFLICT DO NOTHING
            """, [aid, p])
        log_action("add_account", "account", aid, f"إنشاء حساب {username}")
        flash("تم إنشاء الحساب.", "success")
        return redirect(url_for("accounts_page"))
    content = f"""
    <div class="hero"><h1>إضافة مستخدم</h1><p>إنشاء مستخدم جديد وتحديد صلاحياته.</p></div>
    <div class="card">
      <form method="POST">
        <div class="row">
          <div><label>اسم المستخدم</label><input name="username" required></div>
          <div><label>كلمة المرور</label><input type="password" name="password" required></div>
          <div><label>الاسم الكامل</label><input name="full_name"></div>
        </div>
        <div style="margin-top:14px">
          <label>الصلاحيات</label>
          {permissions_checkboxes()}
        </div>
        <div class="actions" style="margin-top:4px">
          <button class="btn btn-primary" type="submit">حفظ</button>
          <a class="btn btn-outline" href="{url_for('accounts_page')}">إلغاء</a>
        </div>
      </form>
    </div>
    """
    return render_page("إضافة مستخدم", content)
