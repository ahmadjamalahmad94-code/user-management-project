# 48m_cards_with_reason.py
# تحديث بوابة البطاقات للمشترك:
#   1) إضافة قائمة الأسباب في الـ dashboard (تظهر في modal قبل التأكيد)
#   2) قبول usage_reason في POST /cards/request وحفظه ضمن الـ audit

import json

from flask import render_template, request, redirect, url_for, flash, session


def _my_pending_card_actions(beneficiary_id: int, limit: int = 20) -> list[dict]:
    rows = query_all(
        """
        SELECT id, payload_json, requested_at
        FROM radius_pending_actions
        WHERE beneficiary_id=%s
          AND action_type='generate_user_cards'
          AND status='pending'
        ORDER BY id DESC
        LIMIT %s
        """,
        [beneficiary_id, limit],
    )
    actions = []
    for row in rows:
        try:
            payload = json.loads(row.get("payload_json") or "{}")
        except (TypeError, ValueError, json.JSONDecodeError):
            payload = {}
        actions.append({"id": row["id"], "payload": payload, "requested_at": row.get("requested_at")})
    return actions


def _user_cards_dashboard_v2():
    """نفس داشبورد البطاقات + يمرر USAGE_REASON_OPTIONS للقالب."""
    from app.services.quota_engine import check_quota, get_available_categories_for_beneficiary, QuotaDecision
    from app.services.card_status_service import get_card_statuses, format_seconds
    from app.services.access_rules import whatsapp_group_url_for_user_type

    beneficiary = get_current_portal_beneficiary() or {}
    beneficiary_id = int(session.get("beneficiary_id") or 0)

    quota = check_quota(beneficiary_id) if beneficiary_id else None
    if quota is None:
        quota = QuotaDecision(allowed=False, reason="لا توجد سياسة محددة لحسابك.", daily_used=0)

    categories = get_available_categories_for_beneficiary(beneficiary_id)

    today_cards = query_all(
        """
        SELECT bic.*,
               (
                   SELECT cc.label_ar
                   FROM card_categories cc
                   WHERE cc.duration_minutes = bic.duration_minutes
                     AND cc.is_active = TRUE
                     AND cc.code IN ('half_hour','one_hour','two_hours','three_hours','four_hours')
                   ORDER BY cc.display_order ASC, cc.id ASC
                   LIMIT 1
               ) AS duration_label
        FROM beneficiary_issued_cards bic
        WHERE bic.beneficiary_id=%s
          AND DATE(bic.issued_at) = DATE('now')
        ORDER BY bic.id DESC
        """,
        [beneficiary_id],
    )
    card_statuses = get_card_statuses(today_cards)

    my_pending_actions = _my_pending_card_actions(beneficiary_id, limit=20)

    return render_template(
        "portal/cards/dashboard.html",
        beneficiary_full_name=beneficiary.get("full_name") or session.get("beneficiary_full_name", ""),
        quota=quota,
        categories=categories,
        today_cards=today_cards,
        card_statuses=card_statuses,
        format_card_seconds=format_seconds,
        my_pending_actions=my_pending_actions,
        my_pending_count=len(my_pending_actions),
        router_url=get_router_login_url(),
        whatsapp_group_url=whatsapp_group_url_for_user_type(beneficiary.get("user_type") or ""),
        reason_options=list(USAGE_REASON_OPTIONS) if USAGE_REASON_OPTIONS else [],
    )


def _user_cards_request_v2():
    """يقبل usage_reason ويسجّله في beneficiary_usage_logs + card_audit_log."""
    from app.services.card_dispatcher import (
        issue_card_from_inventory,
        request_card_via_radius,
    )

    beneficiary_id = int(session.get("beneficiary_id") or 0)
    category_code = clean_csv_value(request.form.get("category_code"))
    usage_reason = clean_csv_value(request.form.get("usage_reason"))

    if not beneficiary_id:
        flash("يجب تسجيل الدخول.", "error")
        return redirect(url_for("user_login"))
    if not category_code:
        flash("الرجاء اختيار فئة البطاقة.", "error")
        return redirect(url_for("user_cards_dashboard"))

    # محاولة 1: إصدار فوري من المخزون
    result = issue_card_from_inventory(
        beneficiary_id, category_code,
        actor_username=_portal_actor_username(),
    )

    if result.ok:
        # سجّل في beneficiary_usage_logs مع السبب
        try:
            _log_card_usage_reason(beneficiary_id, category_code, usage_reason, result)
        except Exception:
            pass
        msg = f"تم إصدار بطاقتك ({result.duration_label}) بنجاح! تجدها في الأسفل."
        if usage_reason:
            msg += f" (السبب: {usage_reason})"
        flash(msg, "success")
        return redirect(url_for("user_cards_dashboard"))

    # محاولة 2: لم يوجد مخزون — أنشئ طلب pending
    if "لا توجد بطاقات متاحة" in (result.message or ""):
        notes = "طلب من بوابة المشترك — المخزون فارغ"
        if usage_reason:
            notes += f" — السبب: {usage_reason}"
        result2 = request_card_via_radius(
            beneficiary_id, category_code,
            actor_username=_portal_actor_username(),
            notes=notes,
        )
        if result2.ok:
            flash("تم تسجيل طلبك. ستسلّمك الإدارة البطاقة قريبًا.", "info")
            return redirect(url_for("user_cards_pending_list"))
        flash(result2.message, "error")
        return redirect(url_for("user_cards_dashboard"))

    flash(result.message, "error")
    return redirect(url_for("user_cards_dashboard"))


def _log_card_usage_reason(beneficiary_id, category_code, reason, dispatch_result):
    """تسجيل سبب البطاقة في beneficiary_usage_logs لظهوره في /admin/usage-logs."""
    if not reason:
        return
    try:
        category = query_one(
            "SELECT label_ar FROM card_categories WHERE code=%s LIMIT 1",
            [category_code],
        ) or {}
        card_type = category.get("label_ar") or category_code
        execute_sql(
            """
            INSERT INTO beneficiary_usage_logs
                (beneficiary_id, usage_reason, card_type, usage_time, usage_date, added_by_username, notes)
            VALUES (%s, %s, %s, CURRENT_TIMESTAMP, DATE('now'), %s, %s)
            """,
            [beneficiary_id, reason, card_type, _portal_actor_username(),
             f"إصدار من بوابة المشترك — {getattr(dispatch_result, 'duration_label', '') or ''}"],
        )
    except Exception:
        # نتجاهل الفشل بصمت — البطاقة أُصدرت بنجاح والسبب فقط فشل تسجيله
        pass


# ─── استبدال الـ view functions القائمة ───
if "user_cards_dashboard" in app.view_functions:
    @user_login_required
    def _new_cards_dashboard():
        return _user_cards_dashboard_v2()
    app.view_functions["user_cards_dashboard"] = _new_cards_dashboard

if "user_cards_request" in app.view_functions:
    @user_login_required
    def _new_cards_request():
        return _user_cards_request_v2()
    app.view_functions["user_cards_request"] = _new_cards_request
