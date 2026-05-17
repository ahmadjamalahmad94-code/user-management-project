# Auto-split from app/legacy.py lines 10290-10410. Loaded by app.legacy.
def _manual_cards_user_access_page():
    beneficiary = get_current_portal_beneficiary()
    access_mode = get_beneficiary_access_mode(beneficiary)
    if access_mode != "cards":
        return _clean_user_internet_access_page()
    latest_card = get_latest_issued_card_for_beneficiary(beneficiary["id"])
    weekly_count = count_beneficiary_card_requests_week(beneficiary["id"])
    daily_count = count_beneficiary_card_requests_today(beneficiary["id"])
    if latest_card:
        router_url = safe(latest_card.get("router_login_url_snapshot") or get_router_login_url())
        card_block = f"""
        <div class="portal-panel" style="margin-top:18px">
          <div class="section-heading"><div><h3>آخر بطاقة صادرة لك</h3><p>يمكنك استخدام الزر للدخول مباشرة إلى الراوتر بالبطاقة الحالية.</p></div></div>
          <div class="grid grid-2">
            <div><label>اسم المستخدم</label><input value="{safe(latest_card.get('card_username'))}" readonly></div>
            <div><label>كلمة المرور</label><input value="{safe(latest_card.get('card_password'))}" readonly></div>
          </div>
          <div class="actions" style="margin-top:16px">
            <form method="POST" action="{router_url}" target="_self" class="inline-form">
              <input type="hidden" name="username" value="{safe(latest_card.get('card_username'))}">
              <input type="hidden" name="password" value="{safe(latest_card.get('card_password'))}">
              <button class="btn btn-primary" type="submit">دخول بالبطاقة</button>
            </form>
            <a class="btn btn-soft" href="{url_for('user_internet_request_page')}">طلب بطاقة جديدة</a>
          </div>
        </div>
        """
    else:
        card_block = f"""
        <div class="portal-panel" style="margin-top:18px">
          <div class="info-note">لا يوجد بطاقة صادرة لك حاليًا. يمكنك طلب بطاقة جديدة من صفحة الطلبات.</div>
        </div>
        """
    content = f"""
    <section class="portal-hero-card compact">
      <div>
        <span class="badge badge-blue">بطاقات الاستخدام</span>
        <h1>حساب البطاقات</h1>
        <p>هذه الصفحة مخصصة للمشتركين الذين يحصلون على بطاقات استخدام مجانية. الحد الحالي: مرة واحدة يوميًا، وبحد أقصى 3 مرات أسبوعيًا.</p>
      </div>
    </section>
    <div class="grid">
      <div class="summary-card"><div class="label">طلبات اليوم</div><div class="value">{daily_count}</div></div>
      <div class="summary-card"><div class="label">طلبات هذا الأسبوع</div><div class="value">{weekly_count}</div></div>
      <div class="summary-card"><div class="label">الحد الأسبوعي</div><div class="value">3</div></div>
    </div>
    {card_block}
    """
    return render_user_page("حساب البطاقات", content)


def _manual_cards_user_request_page():
    beneficiary = get_current_portal_beneficiary()
    access_mode = get_beneficiary_access_mode(beneficiary)
    if access_mode != "cards":
        return _clean_user_internet_request_page()
    if request.method == "POST":
        duration_minutes = int(clean_csv_value(request.form.get("duration_minutes")) or "0")
        if duration_minutes not in {30, 60, 120, 180, 240}:
            flash("يرجى اختيار مدة بطاقة صحيحة.", "error")
            return redirect(url_for("user_internet_request_page"))
        allowed, message = validate_beneficiary_card_request(beneficiary["id"], duration_minutes)
        if not allowed:
            flash(message, "error")
            return redirect(url_for("user_internet_request_page"))
        try:
            issued = issue_manual_card_to_beneficiary(beneficiary, duration_minutes)
            flash(f"تم إصدار بطاقة {issued['duration_label']} لك بنجاح.", "success")
            return redirect(url_for("user_internet_access_page"))
        except Exception as exc:
            flash(f"تعذر إصدار البطاقة: {exc}", "error")
            return redirect(url_for("user_internet_request_page"))
    inventory = get_manual_cards_inventory_counts()
    cards_html = "".join(
        [
            f"""
            <button class="entry-card" type="submit" name="duration_minutes" value="{item['minutes']}" style="text-align:right">
              <span class="entry-icon"><i class="fa-solid fa-ticket"></i></span>
              <strong>{item['label']}</strong>
              <p>المتوفر الآن: {item['available']} بطاقة</p>
            </button>
            """
            for item in inventory
        ]
    )
    daily_count = count_beneficiary_card_requests_today(beneficiary["id"])
    weekly_count = count_beneficiary_card_requests_week(beneficiary["id"])
    content = f"""
    <section class="portal-hero-card compact">
      <div>
        <span class="badge badge-blue">طلب بطاقة</span>
        <h1>اختر مدة البطاقة المطلوبة</h1>
        <p>الطلب متاح حاليًا للمشتركين أصحاب البطاقات فقط. الحد الحالي: طلب واحد في اليوم، وحتى 3 طلبات أسبوعيًا.</p>
      </div>
    </section>
    <div class="grid">
      <div class="summary-card"><div class="label">طلبات اليوم</div><div class="value">{daily_count}</div></div>
      <div class="summary-card"><div class="label">طلبات الأسبوع</div><div class="value">{weekly_count}</div></div>
      <div class="summary-card"><div class="label">المسموح أسبوعيًا</div><div class="value">3</div></div>
    </div>
    <form method="POST" style="margin-top:18px">
      <div class="summary-grid">{cards_html}</div>
    </form>
    """
    return render_user_page("طلب بطاقة", content)


def _clean_portal_access_type_copy(mode: str) -> dict:
    if mode == "cards":
        return {
            "hero_title": "بوابة بطاقات الإنترنت",
            "hero_text": "واجهة بسيطة لمتابعة البطاقات والطلبات والحدود الأسبوعية.",
            "request_label": "طلب بطاقة",
            "internet_label": "البطاقات والحالة",
        }
    return {
        "hero_title": "بوابة حساب الإنترنت",
        "hero_text": "واجهة مخصصة للمشترك لمتابعة الحساب وطلبات الخدمات المرتبطة به.",
        "request_label": "طلب خدمة",
        "internet_label": "حساب الإنترنت",
    }
