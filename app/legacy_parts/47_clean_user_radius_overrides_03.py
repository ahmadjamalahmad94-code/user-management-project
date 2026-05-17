# Continued split from 47_clean_user_radius_overrides.py lines 275-384. Loaded by app.legacy.


def _clean_advradius_app_test_route():
    if request.method == "GET":
        content = f"""
        <div class='hero'>
          <div><h1>اختبار API التطبيق</h1><p>هذه الصفحة تنفذ اختبارًا مباشرًا على واجهة تطبيق المشترك ثم تعرض نتيجة الربط بشكل واضح.</p></div>
        </div>
        <div class='card'>
          <p class='small'>سيتم اختبار <code>/login</code> ثم <code>/details</code> باستخدام إعدادات البيئة الحالية.</p>
          <form method='POST' style='margin-top:16px'>
            <button class='btn btn-accent' type='submit'>تشغيل الاختبار الآن</button>
            <a class='btn btn-soft' href='{url_for("radius_settings_page")}'>العودة إلى إعدادات الربط</a>
          </form>
        </div>
        """
        return render_page("اختبار API التطبيق", content)
    try:
        result = test_advradius_app_connection()
        log_action(
            "test_advradius_app_api",
            "radius_settings",
            None,
            f"AdvRadius App API ok account={json.dumps(result.get('account') or {}, ensure_ascii=False)}",
        )
        content = f"""
        <div class='hero'>
          <div><h1>نجح اختبار AdvRadius App API</h1><p>تم تنفيذ <code>/login</code> ثم <code>/details</code> باستخدام ترويسة <code>adv_auth</code>.</p></div>
          <div class='actions'><a class='btn btn-soft' href='{url_for("radius_settings_page")}'>رجوع</a></div>
        </div>
        <div class='grid grid-2'>
          <div class='card'><h3>بيانات الحساب</h3><pre>{safe(json.dumps(result.get("account") or {}, ensure_ascii=False, indent=2))}</pre></div>
          <div class='card'><h3>استجابة /details</h3><pre>{safe(json.dumps(result.get("details") or {}, ensure_ascii=False, indent=2))}</pre></div>
        </div>
        """
        return render_page("اختبار API التطبيق", content)
    except Exception as exc:
        log_action("test_advradius_app_api_failed", "radius_settings", None, str(exc))
        flash(f"فشل اختبار API التطبيق: {safe(str(exc))}", "error")
        return redirect(url_for("radius_settings_page"))


CARD_DURATION_OPTIONS = [
    {"minutes": 30, "label": "نصف ساعة"},
    {"minutes": 60, "label": "ساعة"},
    {"minutes": 120, "label": "ساعتين"},
    {"minutes": 180, "label": "3 ساعات"},
    {"minutes": 240, "label": "4 ساعات"},
]


def card_duration_label(duration_minutes):
    try:
        minutes = int(duration_minutes or 0)
    except Exception:
        minutes = 0
    for item in CARD_DURATION_OPTIONS:
        if item["minutes"] == minutes:
            return item["label"]
    return f"{minutes} دقيقة" if minutes else "غير محدد"


def get_hotspot_workday_settings():
    row = get_radius_settings_row() or {}
    start_raw = clean_csv_value(row.get("workday_start_time")) or "08:00"
    end_raw = clean_csv_value(row.get("workday_end_time")) or "16:00"
    try:
        start_hour, start_minute = [int(part) for part in start_raw.split(":", 1)]
        start_raw = f"{start_hour:02d}:{start_minute:02d}"
    except Exception:
        start_raw = "08:00"
    try:
        end_hour, end_minute = [int(part) for part in end_raw.split(":", 1)]
        end_raw = f"{end_hour:02d}:{end_minute:02d}"
    except Exception:
        end_raw = "16:00"
    return {"start_time": start_raw, "end_time": end_raw}


def portal_card_options() -> list[dict]:
    workday = portal_workday_context()
    options = [
        {"minutes": 30, "label": "نصف ساعة", "icon": "fa-stopwatch"},
        {"minutes": 60, "label": "ساعة", "icon": "fa-clock"},
        {"minutes": 120, "label": "ساعتين", "icon": "fa-hourglass-half"},
        {"minutes": 180, "label": "3 ساعات", "icon": "fa-business-time"},
        {"minutes": 240, "label": "4 ساعات", "icon": "fa-star"},
    ]
    for item in options:
        item["available"] = workday["is_open"] and workday["remaining_minutes"] >= item["minutes"]
    return options


def validate_beneficiary_card_request(beneficiary_id: int, duration_minutes: int):
    workday = portal_workday_context()
    if not workday["is_open"]:
        return False, f"طلب البطاقات متاح فقط خلال الدوام من {workday['start_time']} إلى {workday['end_time']}."
    if workday["remaining_minutes"] < int(duration_minutes or 0):
        return False, f"الوقت المتبقي حتى نهاية الدوام لا يكفي لإصدار بطاقة {card_duration_label(duration_minutes)}."
    daily_count = count_beneficiary_card_requests_today(beneficiary_id)
    if daily_count >= 1:
        return False, "يمكن طلب بطاقة واحدة فقط في اليوم."
    weekly_count = count_beneficiary_card_requests_week(beneficiary_id)
    if weekly_count >= 3:
        return False, "تم الوصول إلى الحد الأقصى الأسبوعي لطلبات البطاقات."
    available = query_one(
        "SELECT COUNT(*) AS c FROM manual_access_cards WHERE duration_minutes=%s",
        [duration_minutes],
    )
    if int((available or {}).get("c") or 0) <= 0:
        return False, f"لا توجد بطاقات متاحة حاليًا لمدة {card_duration_label(duration_minutes)}."
    return True, ""
