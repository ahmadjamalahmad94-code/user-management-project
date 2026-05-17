# Continued split from 10_manual_cards_services.py lines 128-207. Loaded by app.legacy.


def issue_manual_card_to_beneficiary(beneficiary: dict, duration_minutes: int):
    card = query_one(
        """
        SELECT * FROM manual_access_cards
        WHERE duration_minutes=%s
        ORDER BY id ASC
        LIMIT 1
        """,
        [duration_minutes],
    )
    if not card:
        raise ValueError("لا توجد بطاقة متاحة لهذا القسم حاليًا.")
    request_id = create_internet_service_request(
        beneficiary["id"],
        "request_card",
        {
            "duration_minutes": duration_minutes,
            "card_type": card_duration_label(duration_minutes),
            "delivery_mode": "manual_pool",
        },
    )
    execute_sql(
        """
        INSERT INTO beneficiary_issued_cards (
            beneficiary_id, duration_minutes, card_username, card_password,
            request_id, issued_by, router_login_url_snapshot
        ) VALUES (%s,%s,%s,%s,%s,%s,%s)
        """,
        [
            beneficiary["id"],
            duration_minutes,
            clean_csv_value(card.get("card_username")),
            clean_csv_value(card.get("card_password")),
            request_id,
            session.get("username") or session.get("beneficiary_username") or "system",
            get_router_login_url(),
        ],
    )
    execute_sql("DELETE FROM manual_access_cards WHERE id=%s", [card["id"]])
    execute_sql(
        """
        INSERT INTO beneficiary_usage_logs (
            beneficiary_id, usage_reason, card_type, usage_date, usage_time, notes,
            added_by_account_id, added_by_username
        ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
        """,
        [
            beneficiary["id"],
            "طلب بطاقة",
            card_duration_label(duration_minutes),
            today_local(),
            now_local(),
            f"تم إصدار بطاقة {card_duration_label(duration_minutes)} من المخزون اليدوي",
            session.get("account_id"),
            session.get("username") or session.get("beneficiary_username") or "system",
        ],
    )
    update_internet_service_request(
        request_id,
        status="executed",
        api_endpoint="manual_card_pool",
        api_response={
            "card_username": clean_csv_value(card.get("card_username")),
            "card_password": clean_csv_value(card.get("card_password")),
            "duration_minutes": duration_minutes,
        },
        error_message="",
        executed_at=now_local(),
    )
    log_action("issue_manual_card", "internet_request", request_id, f"Manual card issued for beneficiary {beneficiary['id']}")
    return {
        "request_id": request_id,
        "duration_minutes": duration_minutes,
        "duration_label": card_duration_label(duration_minutes),
        "card_username": clean_csv_value(card.get("card_username")),
        "card_password": clean_csv_value(card.get("card_password")),
        "router_login_url": get_router_login_url(),
    }
