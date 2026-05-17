# Auto-split from app/legacy.py lines 5740-5875. Loaded by app.legacy.
@app.route("/timer")
@login_required
def power_timer_page():
    content = f"""
    <div class="hero">
      <h1>مؤقت الكهرباء</h1>
      <p>مؤقت واحد للدورة الحالية. عند انتهاء الوقت يظهر تنبيه وصوت، ثم يعيد التشغيل تلقائيًا بعد 10 ثوانٍ لنفس المدة المختارة.</p>
    </div>
    <div class="grid-2">
      <div class="card timer-visual-card">
        <div class="actions" style="justify-content:space-between;align-items:flex-start;gap:14px">
          <div>
            <h3 style="margin:0 0 8px 0">الحالة الحالية</h3>
            <div id="timer-page-state" class="timer-state-badge timer-status-stopped">متوقف</div>
          </div>
          <div class="topbar-clock"><i class="fa-regular fa-clock"></i><div><div id="timer-page-live-time">--:--:--</div><small id="timer-page-live-date">--/--/----</small></div></div>
        </div>
        <div class="timer-ring-wrap">
          <div class="timer-ring">
            <svg viewBox="0 0 300 300" aria-hidden="true">
              <defs>
                <linearGradient id="timerRingGradient" x1="0%" y1="0%" x2="100%" y2="100%">
                  <stop offset="0%" stop-color="#35a7e8"></stop>
                  <stop offset="100%" stop-color="#6d4ee8"></stop>
                </linearGradient>
              </defs>
              <circle class="bg" cx="150" cy="150" r="130"></circle>
              <circle id="timer-ring-progress" class="progress" cx="150" cy="150" r="130"></circle>
            </svg>
            <div class="timer-ring-center">
              <div class="timer-ring-label">الوقت المتبقي</div>
              <div id="timer-page-remaining" class="timer-big timer-big-ring">--:--</div>
              <div id="timer-page-phase" class="timer-ring-phase">-</div>
            </div>
          </div>
        </div>
        <div class="timer-progress-strip"><div id="timer-progress-fill" class="timer-progress-fill"></div></div>
        <div class="timer-meta">
          <div class="timer-meta-card"><h4>الدورة الحالية</h4><div class="v" id="timer-page-cycle-minutes">30</div></div>
          <div class="timer-meta-card"><h4>إعادة التشغيل</h4><div class="v"><span id="timer-page-restart">10</span><span style="font-size:18px">ث</span></div></div>
          <div class="timer-meta-card"><h4>النمط</h4><div class="v" style="font-size:20px">تلقائي</div></div>
        </div>
      </div>
      <div class="card">
        <h3 style="margin-top:0">التحكم بالمؤقت</h3>
        <p class="small" style="margin-top:0">واجهة أنيقة للدور الكهربائي مع إعادة تشغيل تلقائي بعد انتهاء كل دورة.</p>
        <div class="row">
          <div><label>مدة الدورة بالدقائق</label><input id="timer-minutes-input" type="number" min="1" step="1" value="30"></div>
          <div><label>إعادة التشغيل التلقائي</label><input value="10 ثوانٍ بعد انتهاء الوقت" disabled></div>
        </div>
        <div class="actions" style="margin-top:4px">
          <button id="timer-start-btn" class="btn btn-primary" type="button" onclick="return startPowerTimer()"><i class="fa-solid fa-play"></i> بدء / إعادة ضبط</button>
          <button id="timer-pause-btn" class="btn btn-accent" type="button" onclick="return pausePowerTimer()" style="display:none"><i class="fa-solid fa-pause"></i> إيقاف مؤقت</button>
          <button id="timer-resume-btn" class="btn btn-secondary" type="button" onclick="return resumePowerTimer()" style="display:none"><i class="fa-solid fa-play"></i> استئناف</button>
          <button id="timer-stop-btn" class="btn btn-danger" type="button" onclick="return stopPowerTimer()" style="display:none"><i class="fa-solid fa-stop"></i> إيقاف نهائي</button>
        </div>
        <div class="info-note" style="margin-top:16px">
          <strong>آلية العمل</strong>
          <div class="small" style="margin-top:6px;line-height:1.8">عند انتهاء الوقت يظهر تنبيه مرئي وصوتي داخل الموقع، ثم يبدأ العد تلقائيًا من جديد بعد 10 ثوانٍ على نفس المدة المختارة.</div>
        </div>
      </div>
    </div>
    """
    return render_page("مؤقت الكهرباء", content)


@app.route("/api/power-timer/status")
@login_required
def power_timer_status_api():
    return jsonify(build_power_timer_status())


@app.route("/api/power-timer/start", methods=["POST"])
@login_required
def power_timer_start_api():
    minutes_raw = clean_csv_value(request.form.get("minutes", "30")) or "30"
    try:
        minutes = max(1, min(24 * 60, int(minutes_raw)))
    except ValueError:
        return jsonify({"ok": False, "message": "قيمة الدقائق غير صحيحة."}), 400
    execute_sql("""
        UPDATE power_timer
        SET duration_minutes=%s, cycle_started_at=CURRENT_TIMESTAMP, paused_remaining_seconds=NULL,
            state='running', auto_restart_delay_seconds=10, updated_by_username=%s, updated_at=CURRENT_TIMESTAMP
        WHERE id=1
    """, [minutes, session.get("username", "")])
    log_action("power_timer_start", "power_timer", 1, f"تشغيل المؤقت لمدة {minutes} دقيقة")
    return jsonify({"ok": True, "message": f"تم تشغيل المؤقت لمدة {minutes} دقيقة."})


@app.route("/api/power-timer/pause", methods=["POST"])
@login_required
def power_timer_pause_api():
    status = build_power_timer_status()
    if status["state"] != "running":
        return jsonify({"ok": False, "message": "المؤقت ليس في حالة تشغيل."}), 400
    remaining = int(status["display_remaining_seconds"] or 0)
    execute_sql("""
        UPDATE power_timer
        SET paused_remaining_seconds=%s, state='paused', updated_by_username=%s, updated_at=CURRENT_TIMESTAMP
        WHERE id=1
    """, [remaining, session.get("username", "")])
    log_action("power_timer_pause", "power_timer", 1, f"إيقاف مؤقت للمؤقت والمتبقي {remaining} ثانية")
    return jsonify({"ok": True, "message": "تم إيقاف المؤقت مؤقتًا."})


@app.route("/api/power-timer/resume", methods=["POST"])
@login_required
def power_timer_resume_api():
    row = get_power_timer_row()
    if (row.get("state") or "") != "paused":
        return jsonify({"ok": False, "message": "المؤقت ليس متوقفًا مؤقتًا."}), 400
    duration_minutes = int(row.get("duration_minutes") or 30)
    duration_seconds = max(60, duration_minutes * 60)
    remaining = int(row.get("paused_remaining_seconds") or duration_seconds)
    elapsed_before_pause = max(0, duration_seconds - remaining)
    execute_sql("""
        UPDATE power_timer
        SET cycle_started_at=(CURRENT_TIMESTAMP - (%s * INTERVAL '1 second')), paused_remaining_seconds=NULL,
            state='running', updated_by_username=%s, updated_at=CURRENT_TIMESTAMP
        WHERE id=1
    """, [elapsed_before_pause, session.get("username", "")])
    log_action("power_timer_resume", "power_timer", 1, "استئناف المؤقت")
    return jsonify({"ok": True, "message": "تم استئناف المؤقت."})


@app.route("/api/power-timer/stop", methods=["POST"])
@login_required
def power_timer_stop_api():
    execute_sql("""
        UPDATE power_timer
        SET state='stopped', cycle_started_at=NULL, paused_remaining_seconds=NULL, updated_by_username=%s, updated_at=CURRENT_TIMESTAMP
        WHERE id=1
    """, [session.get("username", "")])
    log_action("power_timer_stop", "power_timer", 1, "إيقاف نهائي للمؤقت")
    return jsonify({"ok": True, "message": "تم إيقاف المؤقت نهائيًا."})
