# Auto-split from app/legacy.py lines 6903-7375. Loaded by app.legacy.
def internet_request_timeline_html(status_value: str | None) -> str:
    status = clean_csv_value(status_value) or "pending"
    steps = [
        ("pending", "قيد المراجعة"),
        ("approved", "تمت الموافقة"),
        ("executed", "تم التنفيذ"),
    ]
    html_parts = []
    for key, label in steps:
        css = "timeline-step"
        if status == "failed" and key == "executed":
            css += " fail"
        elif status == "rejected" and key in {"approved", "executed"}:
            css += ""
        elif key == status or (status == "approved" and key == "pending") or (status == "executed" and key in {"pending", "approved"}) or (status == "failed" and key in {"pending", "approved"}):
            css += " done" if key != status or status == "executed" else " active"
        html_parts.append(f"<div class='{css}'><i class='fa-solid fa-circle-dot'></i><span>{label}</span></div>")
    if status == "rejected":
        html_parts.append("<div class='timeline-step fail'><i class='fa-solid fa-ban'></i><span>مرفوض</span></div>")
    elif status == "failed":
        html_parts.append("<div class='timeline-step fail'><i class='fa-solid fa-triangle-exclamation'></i><span>فشل التنفيذ</span></div>")
    return "<div class='status-timeline'>" + "".join(html_parts) + "</div>"


def get_radius_settings_row():
    row = query_one("SELECT * FROM radius_api_settings ORDER BY id ASC LIMIT 1")
    if row:
        return row
    execute_sql(
        """
        INSERT INTO radius_api_settings (base_url, admin_username, service_username, api_enabled)
        VALUES ('', '', '', FALSE)
        """
    )
    return query_one("SELECT * FROM radius_api_settings ORDER BY id ASC LIMIT 1")


def load_radius_session():
    row = query_one(
        """
        SELECT api_key, expires_at, last_login_at
        FROM radius_api_sessions
        WHERE api_key IS NOT NULL AND btrim(api_key) <> ''
        ORDER BY id DESC
        LIMIT 1
        """
    )
    if not row:
        return None
    expires_at = row.get("expires_at")
    if expires_at and as_local_dt(expires_at) and as_local_dt(expires_at) < now_local():
        return None
    return row


def save_radius_session(api_key: str):
    execute_sql(
        """
        INSERT INTO radius_api_sessions (api_key, expires_at, last_login_at)
        VALUES (%s, %s, CURRENT_TIMESTAMP)
        """,
        [api_key, default_session_expiry()],
    )


def get_radius_client() -> RadiusApiClient:
    return RadiusApiClient.from_settings(
        get_radius_settings_row(),
        session_loader=load_radius_session,
        session_saver=save_radius_session,
    )


def get_advradius_app_client() -> AdvClientApi:
    return AdvClientApi.from_env()


def test_advradius_app_connection():
    client = get_advradius_app_client()
    session_data = client.login(force=True)
    details_data = client.details(session_data.get("api_key"))
    return summarize_adv_client_test({"account": session_data.get("account") or {}, "details": details_data})


def get_radius_account(beneficiary_id: int):
    return query_one(
        """
        SELECT * FROM beneficiary_radius_accounts
        WHERE beneficiary_id=%s
        LIMIT 1
        """,
        [beneficiary_id],
    )


def upsert_radius_account(
    beneficiary_id: int,
    external_user_id=None,
    external_username=None,
    current_profile_id=None,
    current_profile_name=None,
    original_profile_id=None,
    status=None,
):
    existing = get_radius_account(beneficiary_id)
    params = [
        beneficiary_id,
        clean_csv_value(external_user_id) or None,
        clean_csv_value(external_username) or None,
        clean_csv_value(current_profile_id) or None,
        clean_csv_value(current_profile_name) or None,
        clean_csv_value(original_profile_id) or None,
        clean_csv_value(status) or "active",
    ]
    if existing:
        execute_sql(
            """
            UPDATE beneficiary_radius_accounts
            SET external_user_id=COALESCE(%s, external_user_id),
                external_username=COALESCE(%s, external_username),
                current_profile_id=COALESCE(%s, current_profile_id),
                current_profile_name=COALESCE(%s, current_profile_name),
                original_profile_id=COALESCE(%s, original_profile_id),
                status=COALESCE(%s, status),
                updated_at=CURRENT_TIMESTAMP
            WHERE beneficiary_id=%s
            """,
            params[1:] + [beneficiary_id],
        )
    else:
        execute_sql(
            """
            INSERT INTO beneficiary_radius_accounts (
                beneficiary_id, external_user_id, external_username, current_profile_id,
                current_profile_name, original_profile_id, status
            ) VALUES (%s,%s,%s,%s,%s,%s,%s)
            """,
            params,
        )


def create_internet_service_request(beneficiary_id: int, request_type: str, requested_payload: dict):
    row = execute_sql(
        """
        INSERT INTO internet_service_requests (
            beneficiary_id, request_type, status, requested_payload, requested_by
        ) VALUES (%s,%s,'pending',%s,%s)
        RETURNING id
        """,
        [beneficiary_id, request_type, Json(requested_payload), session.get("username", "")],
        fetchone=True,
    )
    return row["id"] if row else None
