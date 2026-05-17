# Continued split from 34_radius_internet_services.py lines 368-474. Loaded by app.legacy.


def execute_internet_service_request_row(request_row: dict):
    beneficiary = query_one("SELECT * FROM beneficiaries WHERE id=%s", [request_row["beneficiary_id"]])
    if not beneficiary:
        raise RadiusApiError("المستفيد غير موجود.")
    linked_account = get_radius_account(request_row["beneficiary_id"])
    client = get_radius_client()
    endpoint, payload = build_radius_execution_data(request_row, beneficiary, linked_account)
    if endpoint == "/user_insert":
        response = client.create_user(payload)
    elif endpoint == "/generate_user_cards":
        generated = client.generate_user_cards(payload)
        listed = client.get_user_cards({"username": payload.get("username")})
        response = {"generated": generated, "cards": listed}
    elif endpoint == "/user_update":
        response = client.update_user(payload)
    elif endpoint == "/set_add_time":
        response = client.add_time(payload)
    elif endpoint == "/set_add_qouta":
        response = client.add_quota(payload, separate=False)
    elif endpoint == "/set_add_qqouta":
        response = client.add_quota(payload, separate=True)
    elif endpoint == "/set_mac":
        response = client.set_mac(payload)
    elif endpoint == "/user_reset_password":
        response = client.reset_password(payload)
    else:
        raise RadiusApiError("لا يوجد تنفيذ معرف لهذا الطلب.")

    masked_response = mask_sensitive_data(response)
    masked_payload = mask_sensitive_data(payload)
    if clean_csv_value(request_row.get("request_type")) == "create_user":
        external_user_id = clean_csv_value(response.get("user_id")) or clean_csv_value(response.get("id"))
        upsert_radius_account(
            request_row["beneficiary_id"],
            external_user_id=external_user_id,
            external_username=payload.get("username"),
            current_profile_id=clean_csv_value(payload.get("profile_id")) or None,
            current_profile_name=clean_csv_value(payload.get("profile_name")) or clean_csv_value(payload.get("profile")) or None,
            status="active",
        )
    elif clean_csv_value(request_row.get("request_type")) == "temporary_speed_upgrade":
        store_speed_upgrade_record(request_row, payload, linked_account)
    else:
        upsert_radius_account(request_row["beneficiary_id"], external_username=payload.get("username"), status="active")
    update_internet_service_request(
        request_row["id"],
        status="executed",
        api_endpoint=endpoint,
        api_response=masked_response,
        error_message="",
        executed_at=now_local(),
    )
    log_action(
        "execute_radius_action",
        "internet_request",
        request_row["id"],
        f"Execute internet request #{request_row['id']} endpoint={endpoint} payload={json.dumps(masked_payload, ensure_ascii=False)}",
    )
    return endpoint, masked_response


def process_due_speed_restores():
    due_rows = query_all(
        """
        SELECT * FROM temporary_speed_upgrades
        WHERE status='active' AND ends_at <= %s
        ORDER BY id ASC
        """,
        [now_local()],
    )
    if not due_rows:
        return
    client = get_radius_client()
    for row in due_rows:
        old_profile_id = clean_csv_value(row.get("old_profile_id"))
        if not old_profile_id:
            execute_sql("UPDATE temporary_speed_upgrades SET status='failed', updated_at=CURRENT_TIMESTAMP WHERE id=%s", [row["id"]])
            continue
        try:
            response = client.update_user({"username": row["external_username"], "profile_id": old_profile_id})
            execute_sql(
                """
                UPDATE temporary_speed_upgrades
                SET status='restored', restore_api_response=%s, updated_at=CURRENT_TIMESTAMP
                WHERE id=%s
                """,
                [Json(mask_sensitive_data(response)), row["id"]],
            )
            upsert_radius_account(
                row["beneficiary_id"],
                external_username=row["external_username"],
                current_profile_id=old_profile_id,
                original_profile_id=old_profile_id,
                status="active",
            )
            log_action("restore_speed_upgrade", "internet_request", row["id"], f"Restore speed upgrade #{row['id']}")
        except RadiusApiError as exc:
            execute_sql(
                """
                UPDATE temporary_speed_upgrades
                SET status='failed', restore_api_response=%s, updated_at=CURRENT_TIMESTAMP
                WHERE id=%s
                """,
                [Json({"error": str(exc)}), row["id"]],
            )
