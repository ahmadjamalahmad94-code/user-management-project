# Auto-split from app/legacy.py lines 5878-5901. Loaded by app.legacy.
@app.route("/audit-log")
@login_required
@permission_required("view_audit_log")
def audit_log_page():
    page = max(1, int(request.args.get("page", "1") or "1"))
    per_page = 40
    total = query_one("SELECT COUNT(*) AS c FROM audit_logs")["c"]
    pages = max(1, math.ceil(total / per_page))
    offset = (page - 1) * per_page
    rows = query_all("""
        SELECT * FROM audit_logs
        ORDER BY id DESC
        LIMIT %s OFFSET %s
    """, [per_page, offset])
    html = "<div class='hero'><h1>سجل العمليات</h1><p>كل العمليات الحساسة داخل النظام.</p></div><div class='card'><table><thead><tr><th>ID</th><th>المستخدم</th><th>العملية</th><th>الهدف</th><th>الهدف ID</th><th>التفاصيل</th><th>الوقت</th></tr></thead><tbody>"
    for r in rows:
        html += f"<tr><td>{r['id']}</td><td>{safe(r['username_snapshot'])}</td><td>{action_type_label(r['action_type'])}</td><td>{target_type_label(r['target_type'])}</td><td>{safe(r['target_id'])}</td><td>{safe(r['details'])}</td><td>{format_dt_compact(r['created_at'])}</td></tr>"
    html += "</tbody></table>"
    html += "<div class='pagination'>"
    for p in range(1, pages + 1):
        cls = "active" if p == page else ""
        html += f"<a class='{cls}' href='?page={p}'>{p}</a>"
    html += "</div></div>"
    return render_page("سجل العمليات", html)
