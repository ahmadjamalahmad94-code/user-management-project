from __future__ import annotations

from typing import Any

from app import legacy


DONE_STATUSES = {"done", "executed", "approved"}
ADMIN_RECIPIENT = "admin"
BENEFICIARY_RECIPIENT = "beneficiary"


def status_label(status: str | None) -> str:
    value = (status or "pending").lower()
    return {
        "pending": "معلّق",
        "in_progress": "قيد التنفيذ",
        "approved": "معتمد",
        "done": "منجز",
        "executed": "منفّذ",
        "cancelled": "ملغي",
        "rejected": "مرفوض",
        "failed": "فشل",
        "issued": "تم الإصدار",
        "info": "معلومة",
        "warning": "تنبيه",
    }.get(value, status or "معلّق")


def action_label(action_type: str | None) -> str:
    value = action_type or ""
    return {
        "reset_password": "تغيير كلمة مرور",
        "unblock_site": "فتح موقع",
        "speed_upgrade": "رفع سرعة",
        "create_user": "إنشاء يوزر",
        "update_user": "تعديل بيانات",
        "add_time": "إضافة وقت",
        "add_quota_mb": "إضافة كوتة",
        "disconnect": "فصل جلسة",
        "generate_user_cards": "طلب بطاقة",
        "card_issued": "بطاقة جاهزة",
        "card_inventory_empty": "نفاد مخزون بطاقة",
        "access_mode_changed": "تغيير نوع الدخول",
        "beneficiary_created": "مشترك جديد",
        "beneficiary_profile_updated": "تعديل بيانات مشترك",
        "beneficiary_tier_updated": "تغيير صلاحية البطاقات",
        "beneficiary_verification_updated": "تعديل التوثيق",
        "beneficiary_attachment_uploaded": "رفع مرفق",
        "beneficiary_message_added": "رسالة من الإدارة",
        "internet_request_created": "طلب خدمة جديد",
        "internet_request_status": "تحديث طلب خدمة",
    }.get(value, value.replace("_", " ") or "تحديث")


def _safe_int(value: Any) -> int | None:
    try:
        number = int(value)
    except (TypeError, ValueError):
        return None
    return number if number > 0 else None


def _admin_pending_action_href(action_type: str | None, beneficiary_id: int | None = None) -> str:
    request_type = "card" if action_type == "generate_user_cards" else "user"
    href = f"/admin/requests?type={request_type}"
    safe_beneficiary_id = _safe_int(beneficiary_id)
    if safe_beneficiary_id:
        href = f"{href}&beneficiary_id={safe_beneficiary_id}"
    return href


def _notification_href(row: dict[str, Any], *, portal_kind: str = "user") -> str:
    action_url = row.get("action_url") or ""
    if action_url:
        return action_url
    source_type = row.get("source_type") or ""
    source_id = row.get("source_id")
    event_type = row.get("event_type") or ""
    if source_type == "radius_pending_actions":
        if row.get("recipient_type") == ADMIN_RECIPIENT:
            return _admin_pending_action_href(event_type)
        if event_type == "generate_user_cards" or row.get("event_type") == "card_issued":
            return "/card/pending"
        return "/card/pending" if portal_kind == "cards" else "/user/account/requests"
    if source_type == "internet_request" and source_id:
        if row.get("recipient_type") == ADMIN_RECIPIENT:
            return f"/admin/internet-requests/{source_id}"
        return "/user/account/requests"
    if source_type == "issued_card" and row.get("recipient_type") != ADMIN_RECIPIENT:
        return "/card"
    if source_type == "beneficiary":
        safe_source_id = _safe_int(source_id)
        if row.get("recipient_type") == ADMIN_RECIPIENT and safe_source_id:
            return f"/admin/users/{safe_source_id}/profile"
        return "/user/profile"
    if source_type == "user_attachment":
        if row.get("recipient_type") == ADMIN_RECIPIENT and action_url:
            return action_url
        return "/user/profile"
    if source_type == "user_message":
        if row.get("recipient_type") == ADMIN_RECIPIENT and action_url:
            return action_url
        return "/user/profile"
    if row.get("recipient_type") == ADMIN_RECIPIENT:
        return "/admin/notifications"
    return "/card/notifications" if portal_kind == "cards" else "/user/notifications"


def _fetch_notification(notification_id: int) -> dict[str, Any] | None:
    return legacy.query_one("SELECT * FROM notifications WHERE id=%s LIMIT 1", [int(notification_id)])


def _find_existing_notification(source_type: str, source_id: int | None, recipient_type: str, recipient_id: int | None) -> dict[str, Any] | None:
    if not source_type or not source_id:
        return None
    if recipient_type == ADMIN_RECIPIENT:
        return legacy.query_one(
            """
            SELECT id FROM notifications
            WHERE source_type=%s AND source_id=%s AND recipient_type='admin'
            ORDER BY id DESC LIMIT 1
            """,
            [source_type, int(source_id)],
        )
    return legacy.query_one(
        """
        SELECT id FROM notifications
        WHERE source_type=%s AND source_id=%s AND recipient_type='beneficiary' AND recipient_id=%s
        ORDER BY id DESC LIMIT 1
        """,
        [source_type, int(source_id), int(recipient_id or 0)],
    )


def create_notification(
    *,
    recipient_type: str,
    recipient_id: int | None = None,
    title: str,
    body: str = "",
    event_type: str = "",
    status: str = "info",
    source_type: str = "",
    source_id: int | None = None,
    action_url: str = "",
    actor_type: str = "",
    actor_id: int | None = None,
    actor_name: str = "",
    replace_existing: bool = False,
) -> int:
    if recipient_type not in {ADMIN_RECIPIENT, BENEFICIARY_RECIPIENT}:
        return 0
    if recipient_type == BENEFICIARY_RECIPIENT and not _safe_int(recipient_id):
        return 0
    try:
        existing = _find_existing_notification(source_type, source_id, recipient_type, recipient_id) if replace_existing else None
        if existing:
            legacy.execute_sql(
                """
                UPDATE notifications
                SET title=%s, body=%s, event_type=%s, status=%s, action_url=%s,
                    actor_type=%s, actor_id=%s, actor_name=%s, read_at=NULL,
                    created_at=CURRENT_TIMESTAMP
                WHERE id=%s
                """,
                [
                    title,
                    body or "",
                    event_type or "",
                    status or "info",
                    action_url or "",
                    actor_type or "",
                    actor_id,
                    actor_name or "",
                    int(existing["id"]),
                ],
            )
            return int(existing["id"])
        row = legacy.execute_sql(
            """
            INSERT INTO notifications (
                recipient_type, recipient_id, title, body, event_type, status,
                source_type, source_id, action_url, actor_type, actor_id, actor_name
            )
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            RETURNING id
            """,
            [
                recipient_type,
                _safe_int(recipient_id),
                title,
                body or "",
                event_type or "",
                status or "info",
                source_type or "",
                _safe_int(source_id),
                action_url or "",
                actor_type or "",
                _safe_int(actor_id),
                actor_name or "",
            ],
            fetchone=True,
        )
        return int((row or {}).get("id") or 0)
    except Exception:
        return 0


def create_admin_notification(**kwargs: Any) -> int:
    return create_notification(recipient_type=ADMIN_RECIPIENT, recipient_id=None, **kwargs)


def create_beneficiary_notification(beneficiary_id: int, **kwargs: Any) -> int:
    return create_notification(recipient_type=BENEFICIARY_RECIPIENT, recipient_id=beneficiary_id, **kwargs)


def _pending_action_context(action_id: int) -> dict[str, Any] | None:
    return legacy.query_one(
        """
        SELECT a.*, b.full_name, b.phone
        FROM radius_pending_actions a
        LEFT JOIN beneficiaries b ON b.id = a.beneficiary_id
        WHERE a.id=%s
        LIMIT 1
        """,
        [int(action_id)],
    )


def notify_pending_action_created(action_id: int) -> None:
    action = _pending_action_context(action_id)
    if not action:
        return
    action_type = action.get("action_type") or ""
    beneficiary_id = _safe_int(action.get("beneficiary_id"))
    person = action.get("full_name") or action.get("phone") or "مشترك"
    title = f"{action_label(action_type)} جديد"
    body = f"{person} أرسل طلباً بانتظار المراجعة."
    create_admin_notification(
        title=title,
        body=body,
        event_type=action_type,
        status="pending",
        source_type="radius_pending_actions",
        source_id=int(action_id),
        action_url=_admin_pending_action_href(action_type, beneficiary_id),
        actor_type=BENEFICIARY_RECIPIENT if beneficiary_id else "",
        actor_id=beneficiary_id,
        actor_name=person,
    )
    if beneficiary_id:
        create_beneficiary_notification(
            beneficiary_id,
            title="تم استلام طلبك",
            body=f"طلب {action_label(action_type)} وصل للإدارة وهو قيد المراجعة.",
            event_type=action_type,
            status="pending",
            source_type="radius_pending_actions",
            source_id=int(action_id),
            action_url="/card/pending" if action_type == "generate_user_cards" else "/user/account/requests",
            replace_existing=True,
        )


def notify_pending_action_updated(action_id: int, status: str, notes: str = "") -> None:
    action = _pending_action_context(action_id)
    if not action:
        return
    action_type = action.get("action_type") or ""
    beneficiary_id = _safe_int(action.get("beneficiary_id"))
    person = action.get("full_name") or action.get("phone") or "مشترك"
    label = status_label(status)
    create_admin_notification(
        title=f"تحديث {action_label(action_type)}",
        body=f"أصبح طلب {person} بحالة: {label}.",
        event_type=action_type,
        status=status or "info",
        source_type="radius_pending_actions",
        source_id=int(action_id),
        action_url=_admin_pending_action_href(action_type, beneficiary_id),
        actor_type=ADMIN_RECIPIENT,
        actor_name=action.get("executed_by_username") or "",
    )
    if beneficiary_id:
        create_beneficiary_notification(
            beneficiary_id,
            title=f"تحديث على طلبك: {label}",
            body=notes or f"طلب {action_label(action_type)} أصبح بحالة {label}.",
            event_type=action_type,
            status=status or "info",
            source_type="radius_pending_actions",
            source_id=int(action_id),
            action_url="/card/pending" if action_type == "generate_user_cards" else "/user/account/requests",
            replace_existing=True,
        )


def notify_card_issued(beneficiary_id: int, issued_card_id: int, duration_label: str = "", actor_name: str = "") -> None:
    body = f"بطاقتك {duration_label} جاهزة للاستخدام." if duration_label else "بطاقتك جاهزة للاستخدام."
    create_beneficiary_notification(
        beneficiary_id,
        title="بطاقة جاهزة",
        body=body,
        event_type="card_issued",
        status="issued",
        source_type="issued_card",
        source_id=issued_card_id,
        action_url="/card",
        actor_type=ADMIN_RECIPIENT,
        actor_name=actor_name or "",
    )


def notify_inventory_empty(category_label: str = "", category_code: str = "") -> None:
    label = category_label or category_code or "الفئة المطلوبة"
    create_admin_notification(
        title="نفاد مخزون البطاقات",
        body=f"لا توجد بطاقات متاحة لفئة {label}.",
        event_type="card_inventory_empty",
        status="warning",
        source_type="card_inventory",
        source_id=None,
        action_url="/admin/cards/import",
        replace_existing=False,
    )


def notify_access_mode_changed(beneficiary_id: int, new_label: str, actor_name: str = "") -> None:
    create_beneficiary_notification(
        beneficiary_id,
        title="تم تغيير نوع الدخول",
        body=f"تم تحويل حسابك إلى: {new_label}.",
        event_type="access_mode_changed",
        status="info",
        source_type="beneficiary",
        source_id=beneficiary_id,
        action_url="/user/account",
        actor_type=ADMIN_RECIPIENT,
        actor_name=actor_name or "",
    )


def _beneficiary_context(beneficiary_id: int) -> dict[str, Any]:
    return legacy.query_one(
        "SELECT id, full_name, phone, user_type FROM beneficiaries WHERE id=%s LIMIT 1",
        [int(beneficiary_id)],
    ) or {"id": beneficiary_id}


def _beneficiary_display_name(beneficiary_id: int, fallback: str = "مشترك") -> str:
    row = _beneficiary_context(beneficiary_id)
    return row.get("full_name") or row.get("phone") or fallback


def notify_beneficiary_created(beneficiary_id: int, actor_name: str = "") -> None:
    person = _beneficiary_display_name(beneficiary_id)
    create_admin_notification(
        title="مشترك جديد",
        body=f"تمت إضافة {person} إلى سجلات البوابة.",
        event_type="beneficiary_created",
        status="info",
        source_type="beneficiary",
        source_id=beneficiary_id,
        action_url=f"/admin/users/{int(beneficiary_id)}/profile",
        actor_type=ADMIN_RECIPIENT,
        actor_name=actor_name or "",
    )


def notify_beneficiary_profile_updated(beneficiary_id: int, actor_name: str = "", details: str = "") -> None:
    person = _beneficiary_display_name(beneficiary_id)
    create_admin_notification(
        title="تعديل بيانات مشترك",
        body=f"تم تعديل بيانات {person}." + (f" {details}" if details else ""),
        event_type="beneficiary_profile_updated",
        status="info",
        source_type="beneficiary",
        source_id=beneficiary_id,
        action_url=f"/admin/users/{int(beneficiary_id)}/profile",
        actor_type=ADMIN_RECIPIENT,
        actor_name=actor_name or "",
    )
    create_beneficiary_notification(
        beneficiary_id,
        title="تم تحديث بياناتك",
        body="تم تحديث بيانات حسابك في البوابة." + (f" {details}" if details else ""),
        event_type="beneficiary_profile_updated",
        status="info",
        source_type="beneficiary",
        source_id=beneficiary_id,
        action_url="/user/profile",
        actor_type=ADMIN_RECIPIENT,
        actor_name=actor_name or "",
    )


def notify_beneficiary_tier_updated(beneficiary_id: int, tier_label: str, actor_name: str = "") -> None:
    create_beneficiary_notification(
        beneficiary_id,
        title="تم تغيير صلاحية البطاقات",
        body=f"أصبحت صلاحية البطاقات لحسابك: {tier_label}.",
        event_type="beneficiary_tier_updated",
        status="info",
        source_type="beneficiary",
        source_id=beneficiary_id,
        action_url="/card" if tier_label else "/user/profile",
        actor_type=ADMIN_RECIPIENT,
        actor_name=actor_name or "",
    )


def notify_beneficiary_verification_updated(beneficiary_id: int, status_label_text: str, until: str = "", actor_name: str = "") -> None:
    body = f"تم تحديث حالة توثيق حسابك إلى: {status_label_text}."
    if until:
        body += f" صالحة حتى {until}."
    create_beneficiary_notification(
        beneficiary_id,
        title="تم تحديث حالة التوثيق",
        body=body,
        event_type="beneficiary_verification_updated",
        status="info",
        source_type="beneficiary",
        source_id=beneficiary_id,
        action_url="/user/profile",
        actor_type=ADMIN_RECIPIENT,
        actor_name=actor_name or "",
    )


def notify_beneficiary_attachment_uploaded(
    beneficiary_id: int,
    file_name: str,
    actor_name: str = "",
    *,
    attachment_id: int | None = None,
    uploaded_by_kind: str = "",
) -> None:
    person = _beneficiary_display_name(beneficiary_id)
    actor_label = "المشترك" if uploaded_by_kind == BENEFICIARY_RECIPIENT else "الإدارة"
    create_admin_notification(
        title="رفع مرفق جديد",
        body=f"{actor_label} رفع ملفًا في ملف {person}: {file_name}.",
        event_type="beneficiary_attachment_uploaded",
        status="info",
        source_type="user_attachment",
        source_id=attachment_id,
        action_url=f"/admin/users/{int(beneficiary_id)}/profile",
        actor_type=uploaded_by_kind or ADMIN_RECIPIENT,
        actor_id=beneficiary_id if uploaded_by_kind == BENEFICIARY_RECIPIENT else None,
        actor_name=actor_name or "",
    )


def notify_beneficiary_message_added(
    beneficiary_id: int,
    message_kind: str = "note",
    body: str = "",
    actor_name: str = "",
    *,
    message_id: int | None = None,
) -> None:
    kind_label = {
        "note": "ملاحظة",
        "warning": "تحذير",
        "complaint": "شكوى",
        "reminder": "تذكير",
        "info": "تنبيه",
    }.get((message_kind or "").strip().lower(), "رسالة")
    preview = (body or "").strip()
    if len(preview) > 140:
        preview = preview[:137].rstrip() + "..."
    create_beneficiary_notification(
        beneficiary_id,
        title=f"{kind_label} من الإدارة",
        body=preview or "تمت إضافة رسالة جديدة إلى ملفك.",
        event_type="beneficiary_message_added",
        status="info",
        source_type="user_message",
        source_id=message_id,
        action_url="/user/profile",
        actor_type=ADMIN_RECIPIENT,
        actor_name=actor_name or "",
    )


def notify_internet_request_created(request_id: int) -> None:
    row = legacy.query_one(
        """
        SELECT r.id, r.beneficiary_id, r.request_type, b.full_name, b.phone
        FROM internet_service_requests r
        LEFT JOIN beneficiaries b ON b.id = r.beneficiary_id
        WHERE r.id=%s LIMIT 1
        """,
        [int(request_id)],
    )
    if not row:
        return
    person = row.get("full_name") or row.get("phone") or "مشترك"
    create_admin_notification(
        title="طلب خدمة إنترنت جديد",
        body=f"{person} أرسل طلب {action_label(row.get('request_type'))}.",
        event_type="internet_request_created",
        status="pending",
        source_type="internet_request",
        source_id=int(request_id),
        action_url=f"/admin/internet-requests/{request_id}",
        actor_type=BENEFICIARY_RECIPIENT,
        actor_id=_safe_int(row.get("beneficiary_id")),
        actor_name=person,
    )
    if _safe_int(row.get("beneficiary_id")):
        create_beneficiary_notification(
            int(row["beneficiary_id"]),
            title="تم استلام طلب الخدمة",
            body="طلبك وصل للإدارة وسيظهر التحديث هنا.",
            event_type="internet_request_created",
            status="pending",
            source_type="internet_request",
            source_id=int(request_id),
            action_url="/user/account/requests",
            replace_existing=True,
        )


def notify_internet_request_status(request_id: int, status: str, actor_name: str = "", reason: str = "") -> None:
    row = legacy.query_one(
        """
        SELECT r.id, r.beneficiary_id, r.request_type, b.full_name, b.phone
        FROM internet_service_requests r
        LEFT JOIN beneficiaries b ON b.id = r.beneficiary_id
        WHERE r.id=%s LIMIT 1
        """,
        [int(request_id)],
    )
    if not row:
        return
    person = row.get("full_name") or row.get("phone") or "مشترك"
    label = status_label(status)
    create_admin_notification(
        title=f"تحديث طلب إنترنت: {label}",
        body=f"طلب {person} أصبح بحالة {label}.",
        event_type="internet_request_status",
        status=status,
        source_type="internet_request",
        source_id=int(request_id),
        action_url=f"/admin/internet-requests/{request_id}",
        actor_type=ADMIN_RECIPIENT,
        actor_name=actor_name or "",
    )
    if _safe_int(row.get("beneficiary_id")):
        create_beneficiary_notification(
            int(row["beneficiary_id"]),
            title=f"تحديث طلب الخدمة: {label}",
            body=reason or f"طلبك أصبح بحالة {label}.",
            event_type="internet_request_status",
            status=status,
            source_type="internet_request",
            source_id=int(request_id),
            action_url="/user/account/requests",
            actor_type=ADMIN_RECIPIENT,
            actor_name=actor_name or "",
            replace_existing=True,
        )


def mark_notification_read(notification_id: int, recipient_type: str, recipient_id: int | None = None, *, read: bool = True) -> bool:
    if recipient_type not in {ADMIN_RECIPIENT, BENEFICIARY_RECIPIENT}:
        return False
    row = _fetch_notification(notification_id)
    if not row or row.get("recipient_type") != recipient_type:
        return False
    if recipient_type == BENEFICIARY_RECIPIENT and int(row.get("recipient_id") or 0) != int(recipient_id or 0):
        return False
    try:
        legacy.execute_sql(
            "UPDATE notifications SET read_at=%s WHERE id=%s",
            [legacy.now_local().isoformat(sep=" ", timespec="seconds") if read else None, int(notification_id)],
        )
        return True
    except Exception:
        return False


def mark_all_read(recipient_type: str, recipient_id: int | None = None) -> int:
    try:
        if recipient_type == ADMIN_RECIPIENT:
            row = legacy.query_one(
                "SELECT COUNT(*) AS c FROM notifications WHERE recipient_type='admin' AND read_at IS NULL"
            ) or {}
            legacy.execute_sql("UPDATE notifications SET read_at=CURRENT_TIMESTAMP WHERE recipient_type='admin' AND read_at IS NULL")
            return int(row.get("c") or 0)
        if recipient_type == BENEFICIARY_RECIPIENT and _safe_int(recipient_id):
            row = legacy.query_one(
                """
                SELECT COUNT(*) AS c FROM notifications
                WHERE recipient_type='beneficiary' AND recipient_id=%s AND read_at IS NULL
                """,
                [int(recipient_id)],
            ) or {}
            legacy.execute_sql(
                "UPDATE notifications SET read_at=CURRENT_TIMESTAMP WHERE recipient_type='beneficiary' AND recipient_id=%s AND read_at IS NULL",
                [int(recipient_id)],
            )
            return int(row.get("c") or 0)
    except Exception:
        return 0
    return 0


def admin_unread_count() -> int:
    row = legacy.query_one(
        "SELECT COUNT(*) AS c FROM notifications WHERE recipient_type='admin' AND read_at IS NULL"
    ) or {}
    return int(row.get("c") or 0)


def subscriber_unread_count(beneficiary_id: int) -> int:
    if not beneficiary_id:
        return 0
    row = legacy.query_one(
        """
        SELECT COUNT(*) AS c FROM notifications
        WHERE recipient_type='beneficiary' AND recipient_id=%s AND read_at IS NULL
        """,
        [int(beneficiary_id)],
    ) or {}
    return int(row.get("c") or 0)


def notification_count_for_session(session_data: Any) -> int:
    try:
        if session_data.get("portal_type") == "admin" and session_data.get("account_id"):
            return admin_unread_count()
        beneficiary_id = int(session_data.get("beneficiary_id") or 0)
        return subscriber_unread_count(beneficiary_id)
    except Exception:
        return 0


def _preview_item(row: dict[str, Any], *, portal_kind: str = "user") -> dict[str, str]:
    return {
        "title": row.get("title") or action_label(row.get("event_type")),
        "meta": row.get("body") or row.get("created_at") or "",
        "badge": status_label(row.get("status")),
        "href": _notification_href(row, portal_kind=portal_kind),
    }


def admin_notification_preview(limit: int = 10) -> list[dict[str, str]]:
    rows = legacy.query_all(
        """
        SELECT *
        FROM notifications
        WHERE recipient_type='admin'
        ORDER BY CASE WHEN read_at IS NULL THEN 0 ELSE 1 END, id DESC
        LIMIT %s
        """,
        [max(1, int(limit or 10))],
    )
    return [_preview_item(row) for row in rows]


def subscriber_notification_preview(beneficiary_id: int, *, portal_kind: str = "user", limit: int = 10) -> list[dict[str, str]]:
    if not beneficiary_id:
        return []
    rows = legacy.query_all(
        """
        SELECT *
        FROM notifications
        WHERE recipient_type='beneficiary' AND recipient_id=%s
        ORDER BY CASE WHEN read_at IS NULL THEN 0 ELSE 1 END, id DESC
        LIMIT %s
        """,
        [int(beneficiary_id), max(1, int(limit or 10))],
    )
    return [_preview_item(row, portal_kind=portal_kind) for row in rows]


def notification_preview_for_session(session_data: Any, limit: int = 10) -> list[dict[str, str]]:
    try:
        if session_data.get("portal_type") == "admin" and session_data.get("account_id"):
            return admin_notification_preview(limit=limit)
        beneficiary_id = int(session_data.get("beneficiary_id") or 0)
        portal_kind = (
            "cards"
            if session_data.get("beneficiary_access_mode") == "cards" or session_data.get("portal_entry") == "card"
            else "user"
        )
        return subscriber_notification_preview(beneficiary_id, portal_kind=portal_kind, limit=limit)
    except Exception:
        return []


def admin_notification_center(limit: int = 80) -> dict[str, Any]:
    rows = legacy.query_all(
        """
        SELECT *
        FROM notifications
        WHERE recipient_type='admin'
        ORDER BY CASE WHEN read_at IS NULL THEN 0 ELSE 1 END, id DESC
        LIMIT %s
        """,
        [int(limit)],
    )
    unread = [row for row in rows if not row.get("read_at")]
    return {
        "rows": rows,
        "pending": unread,
        "recent": rows,
        "unread_count": len(unread),
        "read_count": len(rows) - len(unread),
    }


def subscriber_notification_center(beneficiary_id: int, limit: int = 80) -> dict[str, Any]:
    rows = legacy.query_all(
        """
        SELECT *
        FROM notifications
        WHERE recipient_type='beneficiary' AND recipient_id=%s
        ORDER BY CASE WHEN read_at IS NULL THEN 0 ELSE 1 END, id DESC
        LIMIT %s
        """,
        [int(beneficiary_id or 0), int(limit)],
    )
    pending_count = len([r for r in rows if not r.get("read_at")])
    done_count = len([r for r in rows if (r.get("status") or "").lower() in DONE_STATUSES])
    return {
        "rows": rows,
        "pending_count": pending_count,
        "done_count": done_count,
        "unread_count": pending_count,
    }
