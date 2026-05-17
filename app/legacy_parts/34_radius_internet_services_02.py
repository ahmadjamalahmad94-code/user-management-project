# Continued split from 34_radius_internet_services.py lines 155-248. Loaded by app.legacy.


def update_internet_service_request(request_id: int, **kwargs):
    if not kwargs:
        return
    allowed = {
        "status",
        "admin_payload",
        "api_endpoint",
        "api_response",
        "error_message",
        "reviewed_by",
        "reviewed_at",
        "executed_at",
        "updated_at",
    }
    fields = []
    values = []
    for key, value in kwargs.items():
        if key not in allowed:
            continue
        fields.append(f"{key}=%s")
        values.append(Json(value or {}) if key in {"admin_payload", "api_response"} else value)
    if "updated_at" not in kwargs:
        fields.append("updated_at=CURRENT_TIMESTAMP")
    values.append(request_id)
    execute_sql(f"UPDATE internet_service_requests SET {', '.join(fields)} WHERE id=%s", values)


def get_internet_request_row(request_id: int):
    return query_one(
        """
        SELECT r.*, b.full_name, b.phone, b.user_type
        FROM internet_service_requests r
        JOIN beneficiaries b ON b.id = r.beneficiary_id
        WHERE r.id=%s
        LIMIT 1
        """,
        [request_id],
    )


def get_request_external_username(request_row: dict, linked_account: dict | None = None) -> str:
    requested_payload = json_safe_dict(request_row.get("requested_payload"))
    admin_payload = json_safe_dict(request_row.get("admin_payload"))
    return (
        clean_csv_value(admin_payload.get("external_username"))
        or clean_csv_value(requested_payload.get("external_username"))
        or clean_csv_value(requested_payload.get("desired_username"))
        or clean_csv_value((linked_account or {}).get("external_username"))
    )


def normalize_internet_request_form(form) -> tuple[int, str, dict]:
    beneficiary_id = int(clean_csv_value(form.get("beneficiary_id", "0")) or "0")
    request_type = clean_csv_value(form.get("request_type", "other")) or "other"
    payload = {
        "desired_username": clean_csv_value(form.get("desired_username")),
        "desired_password": clean_csv_value(form.get("desired_password")),
        "external_username": clean_csv_value(form.get("external_username")),
        "profile_id": clean_csv_value(form.get("profile_id")),
        "profile_name": clean_csv_value(form.get("profile_name")),
        "card_count": clean_csv_value(form.get("card_count")),
        "duration_minutes": clean_csv_value(form.get("duration_minutes")),
        "time_amount": clean_csv_value(form.get("time_amount")),
        "time_unit": clean_csv_value(form.get("time_unit")),
        "quota_amount_mb": clean_csv_value(form.get("quota_amount_mb")),
        "upload_quota_mb": clean_csv_value(form.get("upload_quota_mb")),
        "download_quota_mb": clean_csv_value(form.get("download_quota_mb")),
        "mac_address": clean_csv_value(form.get("mac_address")),
        "new_password": clean_csv_value(form.get("new_password")),
        "notes": clean_csv_value(form.get("notes")),
    }
    return beneficiary_id, request_type, {k: v for k, v in payload.items() if v not in (None, "", [])}


def normalize_admin_request_form(form) -> dict:
    payload = {
        "external_username": clean_csv_value(form.get("external_username")),
        "profile_id": clean_csv_value(form.get("profile_id")),
        "profile_name": clean_csv_value(form.get("profile_name")),
        "original_profile_id": clean_csv_value(form.get("original_profile_id")),
        "duration_minutes": clean_csv_value(form.get("duration_minutes")),
        "card_count": clean_csv_value(form.get("card_count")),
        "time_amount": clean_csv_value(form.get("time_amount")),
        "time_unit": clean_csv_value(form.get("time_unit")),
        "quota_amount_mb": clean_csv_value(form.get("quota_amount_mb")),
        "upload_quota_mb": clean_csv_value(form.get("upload_quota_mb")),
        "download_quota_mb": clean_csv_value(form.get("download_quota_mb")),
        "mac_address": clean_csv_value(form.get("mac_address")),
        "new_password": clean_csv_value(form.get("new_password")),
        "notes": clean_csv_value(form.get("notes")),
    }
    return {k: v for k, v in payload.items() if v not in (None, "", [])}
