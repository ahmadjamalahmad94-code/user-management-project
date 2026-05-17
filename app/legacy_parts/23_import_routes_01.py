# Auto-split from app/legacy.py lines 4723-4919. Loaded by app.legacy.
@app.route("/import")
@login_required
@permission_required("import")
def import_page():
    last_task_id = session.get("last_import_task_id", "")
    last_task = get_import_task(last_task_id) if last_task_id else None
    status_box = ""
    if last_task:
        status_box = f"""
        <div class="card" style="margin-top:14px">
          <h3 style="margin-top:0">آخر مهمة استيراد</h3>
          <div class="info-note">
            <div><strong>الملف:</strong> {safe(last_task.get('filename'))}</div>
            <div><strong>الحالة:</strong> {safe(last_task.get('status'))}</div>
            <div><strong>الرسالة:</strong> {safe(last_task.get('message'))}</div>
          </div>
          <div class="actions" style="margin-top:12px">
            <a class="btn btn-secondary" href="{url_for('import_status_page', task_id=last_task['id'])}"><i class="fa-solid fa-chart-line"></i> فتح شاشة المتابعة</a>
          </div>
        </div>
        """

    content = f"""
    <div class="hero"><h1>استيراد CSV احترافي</h1><p>رفع الملف وتشغيل المعالجة في الخلفية مع شاشة تقدم حية وسجل خطوات مباشر.</p></div>
    <div class="card">
      <form method="POST" action="{url_for('import_csv')}" enctype="multipart/form-data">
        <div class="row">
          <div>
            <label>ملف CSV</label>
            <input type="file" name="csv_file" accept=".csv" required>
            <div class="small" style="margin-top:8px">بعد الضغط على البدء سيتم إنشاء مهمة استيراد مستقلة، ويمكنك متابعة التقدم وسير العمليات مباشرة.</div>
          </div>
        </div>
        <div class="actions" style="margin-top:4px">
          <button class="btn btn-primary" type="submit"><i class="fa-solid fa-play"></i> بدء الاستيراد الاحترافي</button>
          <a class="btn btn-outline" href="{url_for('download_template')}">تنزيل القالب</a>
        </div>
      </form>
    </div>

    <div class="card" style="margin-top:14px">
      <h3 style="margin-top:0">كيف تعمل المعالجة؟</h3>
      <div class="info-note">
        <div>1) يتم قراءة الملف وتحليله أولًا.</div>
        <div>2) يتم تحديد السجلات الجديدة والسجلات التي تحتاج تحديثًا.</div>
        <div>3) تتم المعالجة في الخلفية على دفعات سريعة بدل سجل بسجل.</div>
        <div>4) يمكنك مشاهدة النسبة، عدد المعالجات، وعدد الأخطاء وسجل التنفيذ لحظة بلحظة.</div>
      </div>
    </div>

    {status_box}
    """
    return render_page("استيراد CSV", content)


@app.route("/import_status/<task_id>")
@login_required
@permission_required("import")
def import_status_page(task_id):
    task = get_import_task(task_id)
    if not task:
        flash("مهمة الاستيراد غير موجودة.", "error")
        return redirect(url_for("import_page"))
    # تصميم جديد عبر القالب الحديث
    return render_template("admin/imports/import_status.html", task=task)

    # ⬇️ الكود القديم محفوظ كاحتياط (لن يُنفّذ)
    content = f"""
    <div class="hero"><h1>متابعة الاستيراد المباشرة</h1><p>شاشة حية تعرض التقدم الفعلي وسجل العمليات أثناء المعالجة.</p></div>

    <div class="card">
      <div class="metric-grid">
        <div class="metric-box"><h4>الحالة</h4><div class="num" id="task-status">{safe(task.get('status'))}</div></div>
        <div class="metric-box"><h4>إجمالي السجلات</h4><div class="num" id="task-total">{task.get('total',0)}</div></div>
        <div class="metric-box"><h4>تمت معالجته</h4><div class="num" id="task-processed">{task.get('processed',0)}</div></div>
        <div class="metric-box"><h4>تمت إضافته</h4><div class="num" id="task-inserted">{task.get('inserted',0)}</div></div>
        <div class="metric-box"><h4>تم تحديثه</h4><div class="num" id="task-updated">{task.get('updated',0)}</div></div>
        <div class="metric-box"><h4>الأخطاء</h4><div class="num" id="task-errors">{task.get('error_count',0)}</div></div>
      </div>

      <div style="margin-top:18px">
        <div class="small" style="margin-bottom:6px">نسبة التقدم: <strong id="task-percent">{task.get('percent',0)}%</strong></div>
        <div class="bar-track" style="height:18px"><div id="task-bar" class="bar-fill" style="width:{task.get('percent',0)}%"></div></div>
      </div>

      <div class="info-note" style="margin-top:14px">
        <div><strong>الملف:</strong> {safe(task.get('filename'))}</div>
        <div><strong>الخطوة الحالية:</strong> <span id="task-step">{safe(task.get('current_step'))}</span></div>
        <div><strong>الرسالة:</strong> <span id="task-message">{safe(task.get('message'))}</span></div>
        <div><strong>بدأت:</strong> <span id="task-started">{safe(task.get('started_at'))}</span></div>
        <div><strong>انتهت:</strong> <span id="task-finished">{safe(task.get('finished_at'))}</span></div>
      </div>

      <div class="actions" style="margin-top:4px">
        <a class="btn btn-soft" href="{url_for('import_page')}">الرجوع لصفحة الاستيراد</a>
        <a class="btn btn-secondary" href="{url_for('beneficiaries_page')}">فتح المستفيدين</a>
      </div>
    </div>

    <div class="card" style="margin-top:14px">
      <h3 style="margin-top:0">سير العمليات</h3>
      <div id="task-logs" style="background:#0f172a;color:#e2e8f0;border-radius:16px;padding:14px;max-height:420px;overflow:auto;font-family:Consolas,monospace;font-size:13px;line-height:1.8">
        {''.join(f'<div>{safe(log)}</div>' for log in task.get('logs', [])) or '<div>بانتظار بدء المعالجة...</div>'}
      </div>
    </div>

    <script>
    const taskId = {task_id!r};
    let pollTimer = null;

    function setText(id, value) {{
      const el = document.getElementById(id);
      if (el) el.textContent = value ?? '';
    }}

    function renderLogs(logs) {{
      const box = document.getElementById('task-logs');
      if (!box) return;
      box.innerHTML = (logs && logs.length) ? logs.map(x => `<div>${{x.replace(/</g,'&lt;').replace(/>/g,'&gt;')}}</div>`).join('') : '<div>لا توجد رسائل حتى الآن.</div>';
      box.scrollTop = box.scrollHeight;
    }}

    function refreshTask() {{
      fetch(`/import_progress/${{taskId}}`)
        .then(r => r.json())
        .then(data => {{
          setText('task-status', data.status || '');
          setText('task-total', data.total || 0);
          setText('task-processed', data.processed || 0);
          setText('task-inserted', data.inserted || 0);
          setText('task-updated', data.updated || 0);
          setText('task-errors', data.error_count || 0);
          setText('task-percent', `${{data.percent || 0}}%`);
          setText('task-step', data.current_step || '');
          setText('task-message', data.message || '');
          setText('task-started', data.started_at || '');
          setText('task-finished', data.finished_at || '');
          const bar = document.getElementById('task-bar');
          if (bar) bar.style.width = `${{data.percent || 0}}%`;
          renderLogs(data.logs || []);
          if (['completed', 'failed'].includes(data.status)) {{
            clearInterval(pollTimer);
          }}
        }})
        .catch(() => {{}});
    }}

    refreshTask();
    pollTimer = setInterval(refreshTask, 1200);
    </script>
    """
    return render_page("متابعة الاستيراد", content)


@app.route("/import_progress/<task_id>")
@login_required
@permission_required("import")
def import_progress(task_id):
    task = get_import_task(task_id)
    if not task:
        return jsonify({"error": "not_found"}), 404
    return jsonify(task)
