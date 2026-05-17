# Continued split from 34_radius_internet_services.py lines 249-367. Loaded by app.legacy.


def build_radius_execution_data(request_row: dict, beneficiary_row: dict, linked_account: dict | None = None):
    request_type = clean_csv_value(request_row.get("request_type"))
    requested_payload = json_safe_dict(request_row.get("requested_payload"))
    admin_payload = json_safe_dict(request_row.get("admin_payload"))
    merged = {**requested_payload, **admin_payload}
    username = get_request_external_username(request_row, linked_account)
    if request_type != "create_user" and not username:
        raise RadiusApiError("اسم المستخدم الخارجي مطلوب لتنفيذ هذا الطلب.")

    if request_type == "create_user":
        username = clean_csv_value(merged.get("desired_username")) or clean_csv_value(merged.get("external_username"))
        if not username:
            raise RadiusApiError("يجب تحديد اسم مستخدم خارجي قبل إنشاء المستخدم.")
        payload = {
            "username": username,
            "name": beneficiary_row.get("full_name") or "",
            "fullname": beneficiary_row.get("full_name") or "",
            "full_name": beneficiary_row.get("full_name") or "",
            "mobile": beneficiary_row.get("phone") or "",
            "phone": beneficiary_row.get("phone") or "",
        }
        password = clean_csv_value(merged.get("desired_password")) or clean_csv_value(merged.get("new_password"))
        if password:
            payload["password"] = password
        if clean_csv_value(merged.get("profile_id")):
            payload["profile_id"] = clean_csv_value(merged.get("profile_id"))
        if clean_csv_value(merged.get("profile_name")):
            profile_name = clean_csv_value(merged.get("profile_name"))
            payload["profile_name"] = profile_name
            payload["profile"] = profile_name
        return "/user_insert", payload

    if request_type == "request_card":
        count = max(1, int(clean_csv_value(merged.get("card_count")) or "1"))
        return "/generate_user_cards", {"username": username, "count": count, "cards_count": count}

    if request_type == "temporary_speed_upgrade":
        profile_id = clean_csv_value(merged.get("profile_id"))
        profile_name = clean_csv_value(merged.get("profile_name"))
        if not profile_id and not profile_name:
            raise RadiusApiError("يجب تحديد البروفايل الجديد لتنفيذ رفع السرعة المؤقت.")
        payload = {"username": username}
        if profile_id:
            payload["profile_id"] = profile_id
        if profile_name:
            payload["profile_name"] = profile_name
            payload["profile"] = profile_name
        return "/user_update", payload

    if request_type == "add_time":
        amount = max(1, int(clean_csv_value(merged.get("time_amount")) or "0"))
        unit = clean_csv_value(merged.get("time_unit")) or "minutes"
        payload = {"username": username, "amount": amount, "time": amount, "unit": unit}
        if unit == "days":
            payload["days"] = amount
        elif unit == "hours":
            payload["hours"] = amount
        else:
            payload["minutes"] = amount
        return "/set_add_time", payload

    if request_type == "add_quota":
        upload = clean_csv_value(merged.get("upload_quota_mb"))
        download = clean_csv_value(merged.get("download_quota_mb"))
        if upload or download:
            return "/set_add_qqouta", {
                "username": username,
                "upload_qouta": int(upload or "0"),
                "download_qouta": int(download or "0"),
            }
        amount = max(1, int(clean_csv_value(merged.get("quota_amount_mb")) or "0"))
        return "/set_add_qouta", {"username": username, "qouta": amount, "quota": amount, "mb": amount}

    if request_type == "update_mac":
        mac_address = clean_csv_value(merged.get("mac_address"))
        if not mac_address:
            raise RadiusApiError("عنوان MAC مطلوب لتنفيذ هذا الطلب.")
        return "/set_mac", {"username": username, "mac": mac_address, "action": "set"}

    if request_type == "reset_password":
        payload = {"username": username}
        if clean_csv_value(merged.get("new_password")):
            payload["new_password"] = clean_csv_value(merged.get("new_password"))
        return "/user_reset_password", payload

    raise RadiusApiError("نوع الطلب غير مدعوم للتنفيذ حالياً.")


def store_speed_upgrade_record(request_row: dict, endpoint_payload: dict, linked_account: dict | None):
    merged = {**json_safe_dict(request_row.get("requested_payload")), **json_safe_dict(request_row.get("admin_payload"))}
    duration_minutes = max(1, int(clean_csv_value(merged.get("duration_minutes")) or "60"))
    old_profile_id = clean_csv_value(merged.get("original_profile_id")) or clean_csv_value((linked_account or {}).get("current_profile_id"))
    new_profile_id = clean_csv_value(endpoint_payload.get("profile_id")) or clean_csv_value(endpoint_payload.get("profile_name")) or clean_csv_value(endpoint_payload.get("profile"))
    execute_sql(
        """
        INSERT INTO temporary_speed_upgrades (
            beneficiary_id, external_username, old_profile_id, new_profile_id,
            starts_at, ends_at, status, restore_api_response
        ) VALUES (%s,%s,%s,%s,CURRENT_TIMESTAMP,%s,'active',%s)
        """,
        [
            request_row["beneficiary_id"],
            endpoint_payload.get("username"),
            old_profile_id,
            new_profile_id,
            now_local() + timedelta(minutes=duration_minutes),
            Json({}),
        ],
    )
    upsert_radius_account(
        request_row["beneficiary_id"],
        external_username=endpoint_payload.get("username"),
        current_profile_id=clean_csv_value(endpoint_payload.get("profile_id")) or None,
        current_profile_name=clean_csv_value(endpoint_payload.get("profile_name")) or clean_csv_value(endpoint_payload.get("profile")) or None,
        original_profile_id=old_profile_id,
        status="active",
    )
