# Auto-split from app/legacy.py lines 10191-10287. Loaded by app.legacy.
@app.route("/admin/cards/import", methods=["GET", "POST"])
@admin_login_required
def admin_cards_import_page():
    if request.method == "POST":
        duration_minutes = int(clean_csv_value(request.form.get("duration_minutes")) or "0")
        upload = request.files.get("cards_file")
        if duration_minutes not in {30, 60, 120, 180, 240} or not upload or not clean_csv_value(upload.filename):
            flash("المدة وملف البطاقات حقول مطلوبة.", "error")
            return redirect(url_for("admin_cards_import_page"))
        try:
            inserted = import_manual_access_cards(duration_minutes, upload, clean_csv_value(upload.filename), session.get("username", "admin"))
            log_action("import_manual_cards", "manual_access_cards", 0, f"Imported {inserted} cards for {duration_minutes} minutes")
            flash(f"تم استيراد {inserted} بطاقة لقسم {card_duration_label(duration_minutes)}.", "success")
            return redirect(url_for("admin_cards_inventory_page"))
        except Exception as exc:
            flash(f"تعذر استيراد البطاقات: {exc}", "error")
            return redirect(url_for("admin_cards_import_page"))
    options_html = "".join(
        [f"<option value='{item['minutes']}'>{item['label']}</option>" for item in CARD_DURATION_OPTIONS]
    )
    content = f"""
    <div class="portal-panel">
      <div class="section-heading"><div><h3>استيراد بطاقات الاستخدام</h3><p>ارفع ملف CSV أو XLSX يحتوي عمودين على الأقل: اسم المستخدم ثم كلمة المرور.</p></div></div>
      <form method="POST" enctype="multipart/form-data">
        <div class="grid grid-2">
          <div><label>قسم البطاقات</label><select name="duration_minutes" required><option value="">اختر القسم</option>{options_html}</select></div>
          <div><label>ملف البطاقات</label><input type="file" name="cards_file" accept=".csv,.xlsx,.xlsm" required></div>
        </div>
        <div class="actions" style="margin-top:16px">
          <button class="btn btn-primary" type="submit">استيراد البطاقات</button>
          <a class="btn btn-soft" href="{url_for('admin_cards_inventory_page')}">فتح الجرد</a>
        </div>
      </form>
    </div>
    """
    return render_page("استيراد بطاقات الاستخدام", content)


@app.route("/admin/cards/inventory", methods=["GET"])
@admin_login_required
def admin_cards_inventory_page():
    counts = get_manual_cards_inventory_counts()
    rows = "".join(
        [
            f"<tr><td>{item['label']}</td><td>{item['available']}</td></tr>"
            for item in counts
        ]
    ) or "<tr><td colspan='2'>لا يوجد مخزون بطاقات حاليًا.</td></tr>"
    content = f"""
    <div class="grid">
      {''.join([f"<div class='summary-card'><div class='label'>{item['label']}</div><div class='value'>{item['available']}</div><div class='note'>بطاقات متاحة الآن</div></div>" for item in counts])}
    </div>
    <div class="portal-panel" style="margin-top:18px">
      <div class="actions" style="margin-bottom:14px">
        <a class="btn btn-primary" href="{url_for('admin_cards_import_page')}">استيراد ملف جديد</a>
        <a class="btn btn-soft" href="{url_for('admin_cards_settings_page')}">إعدادات الدخول للراوتر</a>
      </div>
      <div class="table-wrap">
        <table>
          <thead><tr><th>القسم</th><th>المتوفر</th></tr></thead>
          <tbody>{rows}</tbody>
        </table>
      </div>
    </div>
    """
    return render_page("جرد بطاقات الاستخدام", content)


@app.route("/admin/cards/settings", methods=["GET", "POST"])
@admin_login_required
def admin_cards_settings_page():
    settings_row = get_radius_settings_row() or {}
    if request.method == "POST":
        router_login_url = clean_csv_value(request.form.get("router_login_url"))
        execute_sql(
            "UPDATE radius_api_settings SET router_login_url=%s, updated_at=CURRENT_TIMESTAMP WHERE id=1",
            [router_login_url],
        )
        log_action("update_router_login_url", "radius_api_settings", 1, f"router_login_url={router_login_url}")
        flash("تم تحديث رابط تسجيل الدخول للراوتر.", "success")
        return redirect(url_for("admin_cards_settings_page"))
    current_url = safe(settings_row.get("router_login_url") or get_router_login_url())
    content = f"""
    <div class="portal-panel">
      <div class="section-heading"><div><h3>إعداد رابط تسجيل الدخول للراوتر</h3><p>سيُستخدم هذا الرابط في زر دخول البطاقة الذي يظهر للمشترك بعد إصدار البطاقة.</p></div></div>
      <form method="POST">
        <div class="grid">
          <div><label>رابط صفحة الراوتر</label><input name="router_login_url" value="{current_url}" required></div>
        </div>
        <div class="actions" style="margin-top:16px">
          <button class="btn btn-primary" type="submit">حفظ الرابط</button>
          <a class="btn btn-soft" href="{url_for('admin_cards_inventory_page')}">العودة إلى الجرد</a>
        </div>
      </form>
    </div>
    """
    return render_page("إعدادات بطاقات الاستخدام", content)
