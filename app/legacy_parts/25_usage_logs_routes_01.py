# Auto-split from app/legacy.py lines 5122-5338. Loaded by app.legacy.
@app.route("/usage-logs")
@login_required
@permission_required("view")
def usage_logs_page():
    filters = usage_logs_filters_from_request()
    where, params = build_usage_logs_where(filters)

    rows = query_all(f"""
        SELECT l.*, b.full_name, b.phone, b.user_type
        FROM beneficiary_usage_logs l
        JOIN beneficiaries b ON b.id = l.beneficiary_id
        WHERE {where}
        ORDER BY l.usage_time DESC, l.id DESC
        LIMIT 500
    """, params)

    today = today_local()
    week_start = get_week_start(today)
    month_start = get_month_start(today)
    year_start = get_year_start(today)
    week_total = query_one(f"SELECT COUNT(*) AS c FROM beneficiary_usage_logs l JOIN beneficiaries b ON b.id=l.beneficiary_id WHERE {where} AND l.usage_date >= %s", params + [week_start])["c"]
    month_total = query_one(f"SELECT COUNT(*) AS c FROM beneficiary_usage_logs l JOIN beneficiaries b ON b.id=l.beneficiary_id WHERE {where} AND l.usage_date >= %s", params + [month_start])["c"]
    year_total = query_one(f"SELECT COUNT(*) AS c FROM beneficiary_usage_logs l JOIN beneficiaries b ON b.id=l.beneficiary_id WHERE {where} AND l.usage_date >= %s", params + [year_start])["c"]
    archive_total = query_one("SELECT COUNT(*) AS c FROM beneficiary_usage_logs_archive")["c"]

    reason_options = "".join([f"<option value='{safe(x)}' {'selected' if filters['reason']==x else ''}>{safe(x)}</option>" for x in USAGE_REASON_OPTIONS])
    card_options = "".join([f"<option value='{safe(x)}' {'selected' if filters['card_type']==x else ''}>{safe(x)}</option>" for x in CARD_TYPE_OPTIONS])

    row_html = ""
    for idx, r in enumerate(rows, start=1):
        row_html += f"""
        <tr>
          <td>{idx}</td>
          <td>{safe(r['full_name'])}</td>
          <td>{safe(r['phone'])}</td>
          <td>{get_type_label(r['user_type'])}</td>
          <td>{safe(r['usage_reason'])}</td>
          <td>{safe(r['card_type'])}</td>
          <td>{format_dt_short(r['usage_time'])}</td>
          <td>{safe(r['added_by_username']) or '-'}</td>
          <td class='cell-wrap'>{safe(r['notes']) or '-'}</td>
        </tr>
        """
    if not row_html:
        row_html = "<tr><td colspan='9' class='empty-state'>لا توجد بطاقات مطابقة لخيارات البحث الحالية.</td></tr>"

    archive_tools = []
    if has_permission('archive_logs'):
        archive_tools.append(f"""
        <div class='archive-action-card archive-card-orange'>
          <div class='icon'><i class='fa-solid fa-box-archive'></i></div>
          <h4>أرشفة كاملة</h4>
          <p>انقل كل السجل الحالي إلى الأرشيف مع الاحتفاظ بإمكانية الاسترجاع لاحقًا.</p>
          <form method='POST' action='{url_for('archive_usage_logs')}' onsubmit="return confirm('سيتم نقل كل السجل الحالي إلى الأرشيف. متابعة؟')">
            <button class='btn btn-outline' type='submit'><i class='fa-solid fa-box-archive'></i> أرشفة كاملة</button>
          </form>
        </div>
        <div class='archive-action-card archive-card-orange'>
          <div class='icon'><i class='fa-solid fa-calendar-minus'></i></div>
          <h4>أرشفة جزئية</h4>
          <p>انقل السجلات الأقدم من التاريخ الذي تحدده فقط.</p>
          <form method='POST' action='{url_for('archive_usage_logs_before')}' onsubmit="return confirm('سيتم نقل السجلات الأقدم من التاريخ المحدد إلى الأرشيف. متابعة؟')">
            <input type='date' name='before_date' required>
            <button class='btn btn-soft' type='submit'><i class='fa-solid fa-calendar-minus'></i> أرشفة ما قبل تاريخ</button>
          </form>
        </div>
        """)
    if has_permission('backup'):
        archive_tools.append(f"""
        <div class='archive-action-card archive-card-red'>
          <div class='icon'><i class='fa-solid fa-trash-can'></i></div>
          <h4>تنظيف كامل</h4>
          <p>يحذف كل السجل الحالي نهائيًا. استخدمه فقط بعد التأكد أنك لا تحتاج السجلات.</p>
          <form method='POST' action='{url_for('clear_usage_logs')}' onsubmit="return confirm('سيتم حذف كل السجل الحالي نهائيًا. متابعة؟')">
            <button class='btn btn-danger' type='submit'><i class='fa-solid fa-trash-can'></i> تنظيف كامل</button>
          </form>
        </div>
        <div class='archive-action-card archive-card-red'>
          <div class='icon'><i class='fa-solid fa-filter-circle-xmark'></i></div>
          <h4>تنظيف جزئي</h4>
          <p>يحذف فقط السجلات الأقدم من التاريخ الذي تحدده كما هي.</p>
          <form method='POST' action='{url_for('clear_usage_logs_before')}' onsubmit="return confirm('سيتم حذف السجلات الأقدم من التاريخ المحدد نهائيًا. متابعة؟')">
            <input type='date' name='before_date' required>
            <button class='btn btn-soft' type='submit'><i class='fa-solid fa-filter-circle-xmark'></i> تنظيف جزئي</button>
          </form>
        </div>
        """)
    if has_permission('view_archive'):
        archive_tools.append(f"""
        <div class='archive-action-card archive-card-blue'>
          <div class='icon'><i class='fa-solid fa-box-open'></i></div>
          <h4>فتح الأرشيف</h4>
          <p>استعرض السجلات المؤرشفة أو صدّرها أو أرجعها حسب صلاحياتك.</p>
          <div class='actions'><a class='btn btn-secondary' href='{url_for('usage_archive_page')}'><i class='fa-solid fa-box-archive'></i> فتح الأرشيف ({archive_total})</a></div>
        </div>
        """)
    content = f"""
    <div class="hero">
      <h1>سجل البطاقات التفصيلي</h1>
      <p>سجل حي مع أدوات ذكية للتنظيف، الأرشفة، والاستعراض السريع حسب الفلاتر والتاريخ.</p>
    </div>

    <div class="usage-summary-grid">
      <div class="metric-box"><h4>هذا الأسبوع</h4><div class="num">{week_total}</div></div>
      <div class="metric-box"><h4>هذا الشهر</h4><div class="num">{month_total}</div></div>
      <div class="metric-box"><h4>هذه السنة</h4><div class="num">{year_total}</div></div>
      <div class="metric-box"><h4>عدد السجلات بالأرشيف</h4><div class="num">{archive_total}</div></div>
    </div>

    <div class="card glass-card">
      <div class="filter-box">
        <form method="GET">
          <div class="row">
            <div><label>بحث بالاسم أو الجوال</label><input name="q" value="{safe(filters['q'])}" placeholder="مثال: أحمد أحمد أو رقم الجوال"></div>
            <div><label>النوع</label><select name="user_type"><option value="">الكل</option><option value="tawjihi" {"selected" if filters["user_type"]=="tawjihi" else ""}>توجيهي</option><option value="university" {"selected" if filters["user_type"]=="university" else ""}>جامعة</option><option value="freelancer" {"selected" if filters["user_type"]=="freelancer" else ""}>فري لانسر</option></select></div>
            <div><label>سبب البطاقة</label><select name="reason"><option value="">الكل</option>{reason_options}</select></div>
            <div><label>نوع البطاقة</label><select name="card_type"><option value="">الكل</option>{card_options}</select></div>
            <div><label>من تاريخ</label><input type="date" name="date_from" value="{safe(filters['date_from'])}"></div>
            <div><label>إلى تاريخ</label><input type="date" name="date_to" value="{safe(filters['date_to'])}"></div>
          </div>
          <div class="actions" style="margin-top:4px"><button class="btn btn-primary" type="submit"><i class="fa-solid fa-magnifying-glass"></i> بحث</button><a class="btn btn-soft" href="{url_for('usage_logs_page')}">مسح الفلاتر</a></div>
        </form>
      </div>
    </div>

    <div class="card glass-card" style="margin-top:16px">
      <div class="toolbar-card" style="margin-bottom:14px">
        <div><strong>أدوات السجل</strong><div class="small">الأرشفة والتنظيف وفتح الأرشيف بواجهة أوضح وأسرع.</div></div>
      </div>
      <div class="archive-actions-grid">{''.join(archive_tools)}</div>
    </div>

    <div class="card" style="margin-top:16px">
      <div class="table-wrap">
        <table>
          <thead><tr><th>#</th><th>الاسم</th><th>الجوال</th><th>النوع</th><th>سبب البطاقة</th><th>نوع البطاقة</th><th>التاريخ والوقت</th><th>سجلها</th><th>ملاحظات</th></tr></thead>
          <tbody>{row_html}</tbody>
        </table>
      </div>
    </div>
    """
    return render_page("سجل البطاقات", content)
