# 48af_cards_categories_ajax.py
# AJAX endpoints لإدارة فئات البطاقات (add/edit/delete/toggle/get)

from flask import jsonify, request


# الفئات الرسمية المسموحة مع الدقائق المتوافقة
OFFICIAL_DURATION_MAP = {
    "half_hour": 30,
    "one_hour": 60,
    "two_hours": 120,
    "three_hours": 180,
    "four_hours": 240,
}

OFFICIAL_DEFAULTS = {
    "half_hour":   {"label_ar": "نصف ساعة",  "icon": "fa-bolt"},
    "one_hour":    {"label_ar": "ساعة",      "icon": "fa-clock"},
    "two_hours":   {"label_ar": "ساعتان",    "icon": "fa-hourglass-half"},
    "three_hours": {"label_ar": "3 ساعات",   "icon": "fa-bolt-lightning"},
    "four_hours":  {"label_ar": "4 ساعات",   "icon": "fa-fire"},
}


import re as _re_cat

def _build_cat_payload(is_edit=False):
    """يجمع بيانات الفئة من request.form. يرجع (data, error).
       يدعم فئة رسمية (مدة تلقائية) أو فئة مخصصة (كود + مدة من المستخدم)."""
    code = clean_csv_value(request.form.get("code") or "").lower()
    is_custom = code == "custom" or code not in OFFICIAL_DURATION_MAP
    if is_custom:
        # custom: نأخذ الكود والمدة من الفورم
        custom_code = clean_csv_value(request.form.get("custom_code") or "").lower().strip()
        if not custom_code:
            return None, "أدخل كود الفئة المخصصة (لاتيني فقط)."
        if not _re_cat.match(r"^[a-z][a-z0-9_]{1,40}$", custom_code):
            return None, "الكود يجب أن يبدأ بحرف لاتيني، أحرف صغيرة وأرقام و _ فقط (2-40 حرفاً)."
        try:
            duration = int(clean_csv_value(request.form.get("custom_duration") or "0") or 0)
        except (TypeError, ValueError):
            duration = 0
        if duration <= 0 or duration > 24 * 60:
            return None, "أدخل مدة صحيحة بالدقائق (1 إلى 1440)."
        code = custom_code
        defaults = {}
    else:
        duration = OFFICIAL_DURATION_MAP[code]
        defaults = OFFICIAL_DEFAULTS.get(code, {})

    label_ar = clean_csv_value(request.form.get("label_ar") or "") or defaults.get("label_ar")
    icon = clean_csv_value(request.form.get("icon") or "") or defaults.get("icon", "fa-clock")
    try:
        display_order = int(clean_csv_value(request.form.get("display_order") or "") or 100)
    except (TypeError, ValueError):
        display_order = 100
    radius_profile_id = clean_csv_value(request.form.get("radius_profile_id") or "")
    if not label_ar:
        return None, "الاسم بالعربية مطلوب."
    return {
        "code": code,
        "label_ar": label_ar,
        "duration_minutes": duration,
        "display_order": display_order,
        "icon": icon,
        "radius_profile_id": radius_profile_id,
    }, None


# ─── GET /admin/cards/categories/<id>
@app.route("/admin/cards/categories/<int:category_id>")
@admin_login_required
def admin_cards_categories_get(category_id):
    row = query_one("SELECT * FROM card_categories WHERE id=%s", [category_id])
    if not row:
        return jsonify({"ok": False, "message": "الفئة غير موجودة."}), 404
    return jsonify({"ok": True, "data": dict(row)})


# ─── POST /admin/cards/categories/add-ajax
@app.route("/admin/cards/categories/add-ajax", methods=["POST"])
@admin_login_required
def admin_cards_categories_add_ajax():
    data, err = _build_cat_payload()
    if err:
        return jsonify({"ok": False, "message": err}), 400
    if query_one("SELECT id FROM card_categories WHERE code=%s", [data["code"]]):
        return jsonify({"ok": False, "message": f"الكود {data['code']} موجود مسبقاً."}), 400
    execute_sql(
        """
        INSERT INTO card_categories
            (code, label_ar, duration_minutes, display_order, icon, radius_profile_id, is_active)
        VALUES (%s,%s,%s,%s,%s,%s,1)
        """,
        [data["code"], data["label_ar"], data["duration_minutes"],
         data["display_order"], data["icon"], data["radius_profile_id"]],
    )
    log_action("add_card_category", "card_categories", 0, f"code={data['code']} duration={data['duration_minutes']}")
    return jsonify({"ok": True, "message": f"تمت إضافة فئة {data['label_ar']}."})


# ─── POST /admin/cards/categories/<id>/edit
@app.route("/admin/cards/categories/<int:category_id>/edit", methods=["POST"])
@admin_login_required
def admin_cards_categories_edit(category_id):
    row = query_one("SELECT * FROM card_categories WHERE id=%s", [category_id])
    if not row:
        return jsonify({"ok": False, "message": "الفئة غير موجودة."}), 404
    # نسمح بتغيير label_ar/icon/display_order/radius_profile_id فقط (الكود والمدة ثابتان للفئة الرسمية)
    label_ar = clean_csv_value(request.form.get("label_ar") or "")
    icon = clean_csv_value(request.form.get("icon") or "")
    try:
        display_order = int(clean_csv_value(request.form.get("display_order") or "") or 100)
    except (TypeError, ValueError):
        display_order = 100
    radius_profile_id = clean_csv_value(request.form.get("radius_profile_id") or "")
    if not label_ar:
        return jsonify({"ok": False, "message": "الاسم بالعربية مطلوب."}), 400
    execute_sql(
        """
        UPDATE card_categories SET
            label_ar=%s, icon=%s, display_order=%s, radius_profile_id=%s,
            updated_at=CURRENT_TIMESTAMP
        WHERE id=%s
        """,
        [label_ar, icon or "fa-clock", display_order, radius_profile_id, category_id],
    )
    log_action("edit_card_category", "card_categories", category_id, f"label_ar={label_ar}")
    return jsonify({"ok": True, "message": "تم حفظ التعديلات."})


# ─── POST /admin/cards/categories/<id>/delete
@app.route("/admin/cards/categories/<int:category_id>/delete", methods=["POST"])
@admin_login_required
def admin_cards_categories_delete(category_id):
    row = query_one("SELECT id, code FROM card_categories WHERE id=%s", [category_id])
    if not row:
        return jsonify({"ok": False, "message": "الفئة غير موجودة."}), 404
    # نتحقق هل في بطاقات مرتبطة بها
    try:
        cnt = (query_one("SELECT COUNT(*) AS c FROM manual_access_cards WHERE category_code=%s", [row["code"]]) or {}).get("c") or 0
    except Exception:
        cnt = 0
    if cnt and int(cnt) > 0:
        return jsonify({"ok": False, "message": f"لا يمكن حذف الفئة — يوجد {cnt} بطاقة مرتبطة بها. عطّلها بدلاً من الحذف."}), 400
    execute_sql("DELETE FROM card_categories WHERE id=%s", [category_id])
    log_action("delete_card_category", "card_categories", category_id, f"code={row['code']}")
    return jsonify({"ok": True, "message": "تم حذف الفئة."})


# ─── POST /admin/cards/categories/<id>/toggle-ajax
@app.route("/admin/cards/categories/<int:category_id>/toggle-ajax", methods=["POST"])
@admin_login_required
def admin_cards_categories_toggle_ajax(category_id):
    row = query_one("SELECT id, is_active FROM card_categories WHERE id=%s", [category_id])
    if not row:
        return jsonify({"ok": False, "message": "الفئة غير موجودة."}), 404
    new_state = 0 if row.get("is_active") else 1
    execute_sql(
        "UPDATE card_categories SET is_active=%s, updated_at=CURRENT_TIMESTAMP WHERE id=%s",
        [new_state, category_id],
    )
    log_action("toggle_card_category", "card_categories", category_id, f"is_active={new_state}")
    return jsonify({
        "ok": True,
        "message": "تم تفعيل الفئة." if new_state else "تم تعطيل الفئة.",
        "is_active": bool(new_state),
    })
