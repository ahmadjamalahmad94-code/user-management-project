# Auto-split from app/legacy.py lines 5341-5490. Loaded by app.legacy.
@app.route("/usage-archive")
@login_required
@permission_required("view_archive")
def usage_archive_page():
    before_date = parse_date_or_none(request.args.get('date_to'))
    rows = query_all("""
        SELECT a.*, b.full_name, b.phone, b.user_type
        FROM beneficiary_usage_logs_archive a
        LEFT JOIN beneficiaries b ON b.id = a.beneficiary_id
        ORDER BY a.archived_at DESC, a.archive_id DESC
        LIMIT 500
    """)
    row_html = ""
    for idx, r in enumerate(rows, start=1):
        row_html += f"""
        <tr>
          <td>{idx}</td><td>{safe(r.get('full_name')) or '-'}</td><td>{safe(r.get('phone')) or '-'}</td><td>{get_type_label(r.get('user_type'))}</td>
          <td>{safe(r.get('usage_reason'))}</td><td>{safe(r.get('card_type'))}</td><td>{format_dt_short(r.get('usage_time'))}</td>
          <td>{safe(r.get('archived_by_username')) or '-'}</td><td>{format_dt_short(r.get('archived_at'))}</td><td class='cell-wrap'>{safe(r.get('notes')) or '-'}</td>
        </tr>
        """
    action_cards = []
    if has_permission('restore_archive'):
        action_cards.append(f"""
        <div class='archive-action-card archive-card-green'>
          <div class='icon'><i class='fa-solid fa-rotate-left'></i></div>
          <h4>استرجاع كامل</h4><p>أعد كل الأرشيف إلى السجل الحالي مع حذف النسخ من الأرشيف.</p>
          <form method='POST' action='{url_for('restore_archive_logs')}' onsubmit="return confirm('سيتم استرجاع كل الأرشيف إلى السجل الحالي مع حذف النسخ من الأرشيف. متابعة؟')"><button class='btn btn-secondary' type='submit'><i class='fa-solid fa-rotate-left'></i> استرجاع الكل</button></form>
        </div>
        <div class='archive-action-card archive-card-green'>
          <div class='icon'><i class='fa-solid fa-clock-rotate-left'></i></div>
          <h4>استرجاع جزئي</h4><p>استرجع فقط السجلات المؤرشفة الأقدم من التاريخ المحدد.</p>
          <form method='POST' action='{url_for('restore_archive_logs_before')}' onsubmit="return confirm('سيتم استرجاع الأرشيف الأقدم من التاريخ المحدد. متابعة؟')"><input type='date' name='before_date' required><button class='btn btn-soft' type='submit'><i class='fa-solid fa-clock-rotate-left'></i> استرجاع جزئي</button></form>
        </div>
        """)
    if has_permission('export_archive'):
        action_cards.append(f"""
        <div class='archive-action-card archive-card-blue'>
          <div class='icon'><i class='fa-solid fa-file-excel'></i></div>
          <h4>تصدير الأرشيف</h4><p>نزّل نسخة Excel منظمة لكل ما هو محفوظ في الأرشيف.</p>
          <div class='actions'><a class='btn btn-outline' href='{url_for('export_archive_excel')}'><i class='fa-solid fa-file-excel'></i> تصدير Excel</a></div>
        </div>
        """)
    if has_permission('delete_archive'):
        action_cards.append(f"""
        <div class='archive-action-card archive-card-red'>
          <div class='icon'><i class='fa-solid fa-trash-can'></i></div>
          <h4>تنظيف الأرشيف</h4><p>يحذف كل الأرشيف نهائيًا. هذه العملية حساسة وغير قابلة للتراجع.</p>
          <form method='POST' action='{url_for('clear_archive_logs')}' onsubmit="return confirm('سيتم حذف كامل الأرشيف نهائيًا. متابعة؟')"><button class='btn btn-danger' type='submit'><i class='fa-solid fa-trash-can'></i> تنظيف الأرشيف</button></form>
        </div>
        """)
    content = f"""
    <div class='hero'><h1>أرشيف سجل البطاقات</h1><p>منطقة آمنة لحفظ السجلات القديمة مع صلاحيات منفصلة للاستعراض، التصدير، الاسترجاع، والتنظيف.</p></div>
    <div class='card glass-card'><div class='toolbar-card' style='margin-bottom:14px'><div><strong>عمليات الأرشيف</strong><div class='small'>كل عملية هنا مرتبطة بصلاحية مستقلة.</div></div></div><div class='archive-actions-grid'>{''.join(action_cards)}</div></div>
    <div class='card' style='margin-top:16px'><div class='table-wrap'><table><thead><tr><th>#</th><th>الاسم</th><th>الجوال</th><th>النوع</th><th>السبب</th><th>النوع</th><th>وقت الاستخدام</th><th>أرشفها</th><th>وقت الأرشفة</th><th>ملاحظات</th></tr></thead><tbody>{row_html or "<tr><td colspan='10' class='empty-state'>الأرشيف فارغ حاليًا.</td></tr>"}</tbody></table></div></div>
    """
    return render_page("أرشيف سجل البطاقات", content)


@app.route("/usage-archive/export")
@login_required
@permission_required("export_archive")
def export_archive_excel():
    rows = query_all("""
        SELECT a.*, b.full_name, b.phone
        FROM beneficiary_usage_logs_archive a
        LEFT JOIN beneficiaries b ON b.id = a.beneficiary_id
        ORDER BY a.archived_at DESC, a.archive_id DESC
    """)
    wb = Workbook()
    ws = wb.active
    ws.title = "Usage Archive"
    headers = ["الاسم", "الجوال", "سبب البطاقة", "نوع البطاقة", "تاريخ الاستخدام", "وقت الاستخدام", "الملاحظات", "أرشف بواسطة", "وقت الأرشفة"]
    ws.append(headers)
    for r in rows:
        ws.append([
            safe(r.get('full_name')), safe(r.get('phone')), safe(r.get('usage_reason')), safe(r.get('card_type')),
            safe(r.get('usage_date')), format_dt_short(r.get('usage_time')), safe(r.get('notes')),
            safe(r.get('archived_by_username')), format_dt_short(r.get('archived_at')),
        ])
    for cell in ws[1]:
        cell.font = Font(bold=True)
        cell.fill = PatternFill(fill_type='solid', fgColor='DCE8F3')
        cell.alignment = Alignment(horizontal='center')
    for col in ws.columns:
        width = max(len(str(c.value or '')) for c in col) + 2
        ws.column_dimensions[get_column_letter(col[0].column)].width = min(max(width, 14), 34)
    output = io.BytesIO()
    wb.save(output)
    output.seek(0)
    log_action("export_archive", "beneficiary", None, "تصدير أرشيف سجل البطاقات إلى Excel")
    resp = Response(output.getvalue(), mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    resp.headers["Content-Disposition"] = "attachment; filename=usage_archive.xlsx"
    return resp


@app.route("/usage-archive/restore", methods=["POST"])
@login_required
@permission_required("restore_archive")
def restore_archive_logs():
    rows = query_all("SELECT * FROM beneficiary_usage_logs_archive ORDER BY archive_id")
    restored = 0
    for r in rows:
        execute_sql("""
            INSERT INTO beneficiary_usage_logs
            (beneficiary_id, usage_reason, card_type, usage_date, usage_time, notes, added_by_account_id, added_by_username)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
        """, [r.get('beneficiary_id'), r.get('usage_reason'), r.get('card_type'), r.get('usage_date'), r.get('usage_time'), r.get('notes'), r.get('added_by_account_id'), r.get('added_by_username')])
        restored += 1
    execute_sql("DELETE FROM beneficiary_usage_logs_archive")
    log_action("restore_archive", "beneficiary", None, f"استرجاع كامل من الأرشيف: {restored} سجل")
    flash(f"تم استرجاع {restored} سجل من الأرشيف إلى السجل الحالي.", "success")
    return redirect(url_for("usage_archive_page"))


@app.route("/usage-archive/restore-before", methods=["POST"])
@login_required
@permission_required("restore_archive")
def restore_archive_logs_before():
    before_date = parse_date_or_none(request.form.get('before_date'))
    if not before_date:
        flash("اختر تاريخًا صحيحًا للاسترجاع الجزئي.", "error")
        return redirect(url_for("usage_archive_page"))
    rows = query_all("SELECT * FROM beneficiary_usage_logs_archive WHERE usage_date < %s ORDER BY archive_id", [before_date])
    restored = 0
    archive_ids = []
    for r in rows:
        execute_sql("""
            INSERT INTO beneficiary_usage_logs
            (beneficiary_id, usage_reason, card_type, usage_date, usage_time, notes, added_by_account_id, added_by_username)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
        """, [r.get('beneficiary_id'), r.get('usage_reason'), r.get('card_type'), r.get('usage_date'), r.get('usage_time'), r.get('notes'), r.get('added_by_account_id'), r.get('added_by_username')])
        restored += 1
        archive_ids.append(r['archive_id'])
    if archive_ids:
        execute_sql("DELETE FROM beneficiary_usage_logs_archive WHERE archive_id = ANY(%s)", [archive_ids])
    log_action("restore_archive", "beneficiary", None, f"استرجاع جزئي من الأرشيف قبل {before_date}: {restored} سجل")
    flash(f"تم استرجاع {restored} سجل أقدم من {before_date}.", "success")
    return redirect(url_for("usage_archive_page"))


@app.route("/usage-archive/clear", methods=["POST"])
@login_required
@permission_required("delete_archive")
def clear_archive_logs():
    deleted = query_one("SELECT COUNT(*) AS c FROM beneficiary_usage_logs_archive")["c"]
    execute_sql("DELETE FROM beneficiary_usage_logs_archive")
    log_action("clear_archive", "beneficiary", None, f"تنظيف كامل للأرشيف: {deleted} سجل")
    flash(f"تم حذف {deleted} سجل من الأرشيف.", "success")
    return redirect(url_for("usage_archive_page"))
