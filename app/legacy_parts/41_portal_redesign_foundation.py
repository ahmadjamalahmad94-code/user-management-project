# Auto-split from app/legacy.py lines 8865-9104. Loaded by app.legacy.
BASE_TEMPLATE = BASE_TEMPLATE.replace(
    """<a href="{{ url_for('radius_settings_page') }}" class="{% if path == '/admin/radius/settings' %}active{% endif %}"><i class="fa-solid fa-sliders"></i><span class="nav-label">إعدادات الربط</span></a>""",
    """<a href="{{ url_for('radius_settings_page') }}" class="{% if path == '/admin/radius/settings' %}active{% endif %}"><i class="fa-solid fa-sliders"></i><span class="nav-label">إعدادات الربط</span></a>
        <a href="{{ url_for('advradius_app_test_route') }}" class="{% if path == '/admin/radius/app-test' %}active{% endif %}"><i class="fa-solid fa-mobile-screen-button"></i><span class="nav-label">اختبار API التطبيق</span></a>""",
)


def portal_now_hebron() -> datetime:
    try:
        return datetime.now(ZoneInfo("Asia/Hebron"))
    except Exception:
        return now_local()


def portal_workday_context() -> dict:
    now_dt = portal_now_hebron()
    settings_row = get_radius_settings_row() or {}
    start_raw = clean_csv_value(settings_row.get("workday_start_time")) or "08:00"
    end_raw = clean_csv_value(settings_row.get("workday_end_time")) or "16:00"
    try:
        start_hour, start_minute = [int(part) for part in start_raw.split(":", 1)]
    except Exception:
        start_hour, start_minute = 8, 0
        start_raw = "08:00"
    try:
        end_hour, end_minute = [int(part) for part in end_raw.split(":", 1)]
    except Exception:
        end_hour, end_minute = 16, 0
        end_raw = "16:00"
    opening_dt = now_dt.replace(hour=start_hour, minute=start_minute, second=0, microsecond=0)
    closing_dt = now_dt.replace(hour=end_hour, minute=end_minute, second=0, microsecond=0)
    is_open = opening_dt <= now_dt < closing_dt
    remaining_minutes = max(0, int((closing_dt - now_dt).total_seconds() // 60)) if is_open else 0
    return {
        "now": now_dt,
        "opening": opening_dt,
        "closing": closing_dt,
        "start_time": start_raw,
        "end_time": end_raw,
        "remaining_minutes": remaining_minutes,
        "remaining_hours": round(remaining_minutes / 60, 1) if remaining_minutes > 0 else 0,
        "is_open": is_open,
    }


def portal_next_friday_date() -> date:
    current_date = portal_now_hebron().date()
    days_until_friday = (4 - current_date.weekday()) % 7
    if days_until_friday == 0:
        return current_date
    return current_date + timedelta(days=days_until_friday)


def portal_card_options() -> list[dict]:
    workday = portal_workday_context()
    options = [
        {"minutes": 30, "label": "نص ساعة", "icon": "fa-stopwatch"},
        {"minutes": 60, "label": "ساعة", "icon": "fa-clock"},
        {"minutes": 120, "label": "ساعتين", "icon": "fa-hourglass-half"},
        {"minutes": 180, "label": "3 ساعات", "icon": "fa-business-time"},
    ]
    for item in options:
        item["available"] = workday["remaining_minutes"] >= item["minutes"]
    return options


def portal_card_options_html(selected_minutes: str = "60") -> str:
    cards = []
    for item in portal_card_options():
        state_class = " active" if str(item["minutes"]) == str(selected_minutes) else ""
        disabled_class = "" if item["available"] else " disabled"
        note = "مناسبة للوقت المتبقي" if item["available"] else "أطول من الوقت المتبقي"
        cards.append(
            f"""
            <button class="duration-card{state_class}{disabled_class}" type="button" onclick="document.getElementById('portal-duration').value='{item['minutes']}'; this.closest('.duration-grid').querySelectorAll('.duration-card').forEach(function(el){{el.classList.remove('active');}}); this.classList.add('active');">
              <i class="fa-solid {item['icon']}"></i>
              <strong>{item['label']}</strong>
              <small>{note}</small>
            </button>
            """
        )
    return "<div class='duration-grid'>" + "".join(cards) + "</div>"


def portal_access_type_copy(mode: str) -> dict:
    if mode == "cards":
        return {
            "hero_title": "بوابة بطاقات الإنترنت",
            "hero_text": "واجهة مخصصة لإدارة طلبات البطاقات ومتابعة الحدود الأسبوعية.",
            "request_label": "طلب بطاقة",
            "internet_label": "البطاقات والحالة",
        }
    return {
        "hero_title": "بوابة حساب الإنترنت",
        "hero_text": "واجهة خدمات المشترك لمتابعة الحساب وطلب الخدمات المتعلقة باليوزر.",
        "request_label": "طلب خدمة",
        "internet_label": "حساب الإنترنت",
    }


USER_BASE_TEMPLATE = _legacy_template_text('41_portal_redesign_foundation.USER_BASE_TEMPLATE.html')


def render_user_page(title, content):
    beneficiary = get_current_portal_beneficiary() if session.get("portal_type") == "beneficiary" else None
    access_mode = get_beneficiary_access_mode(beneficiary)
    return render_template_string(
        USER_BASE_TEMPLATE,
        title=title,
        content=content,
        portal_access_mode=access_mode,
        portal_access_label=get_beneficiary_access_label(beneficiary),
        portal_copy=portal_access_type_copy(access_mode),
        hebron_now=portal_now_hebron(),
    )


@app.route("/user/register", methods=["GET", "POST"])
def user_register():
    if request.method == "POST":
        flash("تم استلام طلب الاشتراك داخليًا. ستقوم الإدارة بمراجعة البيانات وإنشاء حساب البوابة عند الاعتماد.", "info")
        return redirect(url_for("user_register"))
    return render_template("auth/user_register.html")
