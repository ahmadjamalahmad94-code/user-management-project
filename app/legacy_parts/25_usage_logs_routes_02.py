# Continued split from 25_usage_logs_routes.py lines 144-218. Loaded by app.legacy.


def _archive_usage_rows(before_date=None):
    conditions = []
    params = []
    if before_date:
        conditions.append("usage_date < %s")
        params.append(before_date)
    where_sql = ("WHERE " + " AND ".join(conditions)) if conditions else ""
    moved = execute_sql(f"""
        WITH moved AS (
            INSERT INTO beneficiary_usage_logs_archive (
                original_log_id, beneficiary_id, usage_reason, card_type, usage_date, usage_time, notes,
                added_by_account_id, added_by_username, archived_at, archived_by_account_id, archived_by_username
            )
            SELECT id, beneficiary_id, usage_reason, card_type, usage_date, usage_time, notes,
                   added_by_account_id, added_by_username, CURRENT_TIMESTAMP, %s, %s
            FROM beneficiary_usage_logs
            {where_sql}
            RETURNING original_log_id
        )
        SELECT COUNT(*) AS c FROM moved
    """, [session.get('account_id'), session.get('username', '')] + params, fetchone=True)
    execute_sql(f"DELETE FROM beneficiary_usage_logs {where_sql}", params)
    return int((moved or {}).get('c') or 0)


@app.route("/usage-logs/archive", methods=["POST"])
@login_required
@permission_required("archive_logs")
def archive_usage_logs():
    moved = _archive_usage_rows()
    log_action("archive_logs", "beneficiary", None, f"أرشفة كاملة لسجل البطاقات: {moved} سجل")
    flash(f"تمت أرشفة {moved} سجل بنجاح.", "success")
    return redirect(url_for("usage_logs_page"))


@app.route("/usage-logs/archive-before", methods=["POST"])
@login_required
@permission_required("archive_logs")
def archive_usage_logs_before():
    before_date = parse_date_or_none(request.form.get("before_date"))
    if not before_date:
        flash("اختر تاريخًا صحيحًا للأرشفة الجزئية.", "error")
        return redirect(url_for("usage_logs_page"))
    moved = _archive_usage_rows(before_date)
    log_action("archive_logs", "beneficiary", None, f"أرشفة جزئية قبل {before_date}: {moved} سجل")
    flash(f"تمت أرشفة {moved} سجل أقدم من {before_date}.", "success")
    return redirect(url_for("usage_logs_page"))


@app.route("/usage-logs/clear", methods=["POST"])
@login_required
@permission_required("backup")
def clear_usage_logs():
    deleted = query_one("SELECT COUNT(*) AS c FROM beneficiary_usage_logs")["c"]
    execute_sql("DELETE FROM beneficiary_usage_logs")
    log_action("clear_usage_logs", "beneficiary", None, f"تنظيف كامل لسجل البطاقات: {deleted} سجل")
    flash(f"تم حذف {deleted} سجل من السجل الحالي.", "success")
    return redirect(url_for("usage_logs_page"))


@app.route("/usage-logs/clear-before", methods=["POST"])
@login_required
@permission_required("backup")
def clear_usage_logs_before():
    before_date = parse_date_or_none(request.form.get("before_date"))
    if not before_date:
        flash("اختر تاريخًا صحيحًا للتنظيف الجزئي.", "error")
        return redirect(url_for("usage_logs_page"))
    deleted = query_one("SELECT COUNT(*) AS c FROM beneficiary_usage_logs WHERE usage_date < %s", [before_date])["c"]
    execute_sql("DELETE FROM beneficiary_usage_logs WHERE usage_date < %s", [before_date])
    log_action("clear_usage_logs", "beneficiary", None, f"تنظيف جزئي قبل {before_date}: {deleted} سجل")
    flash(f"تم حذف {deleted} سجل أقدم من {before_date}.", "success")
    return redirect(url_for("usage_logs_page"))
