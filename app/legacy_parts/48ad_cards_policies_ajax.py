# 48ad_cards_policies_ajax.py
# AJAX endpoints لسياسات حصص البطاقات (add/edit/delete/toggle/get)

from flask import jsonify, request


def _intornone(v):
    v = clean_csv_value(v)
    return int(v) if v else None


def _time_or_none(v):
    value = clean_csv_value(v)
    if not value:
        return None
    parts = value.split(":", 1)
    if len(parts) != 2:
        raise ValueError
    hour, minute = int(parts[0]), int(parts[1])
    if not (0 <= hour <= 23 and 0 <= minute <= 59):
        raise ValueError
    return f"{hour:02d}:{minute:02d}"


def _build_policy_payload():
    """يجمع حقول السياسة من request.form ويتحقق منها. يرجع (data, error_message)."""
    scope = clean_csv_value(request.form.get("scope") or "default")
    if scope not in {"default", "user", "group"}:
        return None, "نطاق غير صالح."
    try:
        target_id = _intornone(request.form.get("target_id"))
        daily_limit = _intornone(request.form.get("daily_limit"))
        weekly_limit = _intornone(request.form.get("weekly_limit"))
        priority = int(clean_csv_value(request.form.get("priority") or "100"))
        valid_time_from = _time_or_none(request.form.get("valid_time_from"))
        valid_time_until = _time_or_none(request.form.get("valid_time_until"))
    except (TypeError, ValueError):
        return None, "قيمة غير صالحة في الحدود أو الأولوية أو ساعات الدوام."
    if scope in {"user", "group"} and not target_id:
        return None, "يلزم تحديد ID المستهدف للنطاق المختار."
    if bool(valid_time_from) ^ bool(valid_time_until):
        return None, "حدد بداية ونهاية ساعات الدوام معًا، أو اتركهما فارغتين."
    return {
        "scope": scope,
        "target_id": target_id,
        "daily_limit": daily_limit,
        "weekly_limit": weekly_limit,
        "priority": priority,
        "allowed_days": clean_csv_value(request.form.get("allowed_days")),
        "allowed_category_codes": clean_csv_value(request.form.get("allowed_category_codes")),
        "valid_from": clean_csv_value(request.form.get("valid_from")) or None,
        "valid_until": clean_csv_value(request.form.get("valid_until")) or None,
        "valid_time_from": valid_time_from,
        "valid_time_until": valid_time_until,
        "notes": clean_csv_value(request.form.get("notes")),
    }, None


# ─── GET /admin/cards/policies/<id> — قراءة سياسة لتعبئة modal التعديل
@app.route("/admin/cards/policies/<int:policy_id>")
@admin_login_required
def admin_cards_policies_get(policy_id):
    row = query_one("SELECT * FROM card_quota_policies WHERE id=%s", [policy_id])
    if not row:
        return jsonify({"ok": False, "message": "السياسة غير موجودة."}), 404
    return jsonify({"ok": True, "data": dict(row)})


# ─── POST /admin/cards/policies/add-ajax
@app.route("/admin/cards/policies/add-ajax", methods=["POST"])
@admin_login_required
def admin_cards_policies_add_ajax():
    data, err = _build_policy_payload()
    if err:
        return jsonify({"ok": False, "message": err}), 400
    execute_sql(
        """
        INSERT INTO card_quota_policies
            (scope, target_id, daily_limit, weekly_limit, allowed_days,
             allowed_category_codes, priority, valid_from, valid_until,
             valid_time_from, valid_time_until, notes, is_active, created_by_account_id)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,TRUE,%s)
        """,
        [data["scope"], data["target_id"], data["daily_limit"], data["weekly_limit"],
         data["allowed_days"], data["allowed_category_codes"], data["priority"],
         data["valid_from"], data["valid_until"], data["valid_time_from"], data["valid_time_until"],
         data["notes"], session.get("account_id")],
    )
    log_action(
        "add_quota_policy", "card_quota_policies", 0,
        f"scope={data['scope']} target={data['target_id']} daily={data['daily_limit']}",
    )
    return jsonify({"ok": True, "message": "تمت إضافة السياسة."})


# ─── POST /admin/cards/policies/<id>/edit
@app.route("/admin/cards/policies/<int:policy_id>/edit", methods=["POST"])
@admin_login_required
def admin_cards_policies_edit(policy_id):
    if not query_one("SELECT id FROM card_quota_policies WHERE id=%s", [policy_id]):
        return jsonify({"ok": False, "message": "السياسة غير موجودة."}), 404
    data, err = _build_policy_payload()
    if err:
        return jsonify({"ok": False, "message": err}), 400
    execute_sql(
        """
        UPDATE card_quota_policies SET
            scope=%s, target_id=%s, daily_limit=%s, weekly_limit=%s,
            allowed_days=%s, allowed_category_codes=%s, priority=%s,
            valid_from=%s, valid_until=%s, valid_time_from=%s, valid_time_until=%s,
            notes=%s, updated_at=CURRENT_TIMESTAMP
        WHERE id=%s
        """,
        [data["scope"], data["target_id"], data["daily_limit"], data["weekly_limit"],
         data["allowed_days"], data["allowed_category_codes"], data["priority"],
         data["valid_from"], data["valid_until"], data["valid_time_from"], data["valid_time_until"],
         data["notes"], policy_id],
    )
    log_action("edit_quota_policy", "card_quota_policies", policy_id, f"scope={data['scope']}")
    return jsonify({"ok": True, "message": "تم حفظ التعديلات."})


# ─── POST /admin/cards/policies/<id>/delete
@app.route("/admin/cards/policies/<int:policy_id>/delete", methods=["POST"])
@admin_login_required
def admin_cards_policies_delete(policy_id):
    row = query_one("SELECT id FROM card_quota_policies WHERE id=%s", [policy_id])
    if not row:
        return jsonify({"ok": False, "message": "السياسة غير موجودة."}), 404
    execute_sql("DELETE FROM card_quota_policies WHERE id=%s", [policy_id])
    log_action("delete_quota_policy", "card_quota_policies", policy_id, "")
    return jsonify({"ok": True, "message": "تم حذف السياسة."})


# ─── POST /admin/cards/policies/<id>/toggle-ajax — نسخة JSON من toggle
@app.route("/admin/cards/policies/<int:policy_id>/toggle-ajax", methods=["POST"])
@admin_login_required
def admin_cards_policies_toggle_ajax(policy_id):
    row = query_one("SELECT id, is_active FROM card_quota_policies WHERE id=%s", [policy_id])
    if not row:
        return jsonify({"ok": False, "message": "السياسة غير موجودة."}), 404
    new_state = 0 if row.get("is_active") else 1
    execute_sql(
        "UPDATE card_quota_policies SET is_active=%s, updated_at=CURRENT_TIMESTAMP WHERE id=%s",
        [new_state, policy_id],
    )
    log_action("toggle_quota_policy", "card_quota_policies", policy_id, f"is_active={new_state}")
    return jsonify({
        "ok": True,
        "message": "تم تفعيل السياسة." if new_state else "تم تعطيل السياسة.",
        "is_active": bool(new_state),
    })
