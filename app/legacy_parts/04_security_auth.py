# Auto-split from app/legacy.py lines 1344-1420. Loaded by app.legacy.
from app.security.passwords import (
    admin_password_hash,
    is_legacy_sha256_hash,
    sha256_text,
    verify_admin_password,
)


def maybe_upgrade_admin_password(account_id: int, password: str, stored_hash: str | None):
    if account_id and is_legacy_sha256_hash(stored_hash):
        execute_sql(
            "UPDATE app_accounts SET password_hash=%s WHERE id=%s",
            [admin_password_hash(password), account_id],
        )


def get_initial_admin_password() -> str:
    configured = clean_csv_value(os.getenv("HOBEHUB_ADMIN_PASSWORD", ""))
    if configured:
        return configured
    if is_local_demo_mode() or env_flag("HOBEHUB_ALLOW_DEFAULT_ADMIN_PASSWORD"):
        return "123456"
    return ""


def auth_failure_key(area: str, username: str) -> str:
    remote_addr = request.headers.get("X-Forwarded-For", request.remote_addr or "").split(",", 1)[0].strip()
    return f"{area}:{remote_addr}:{clean_csv_value(username).lower()}"


def is_auth_limited(key: str) -> bool:
    record = AUTH_FAILURES.get(key)
    if not record:
        return False
    locked_until = record.get("locked_until")
    if locked_until and locked_until > datetime.now(timezone.utc):
        return True
    first_seen = record.get("first_seen")
    if first_seen and first_seen < datetime.now(timezone.utc) - timedelta(minutes=AUTH_LOCK_MINUTES):
        AUTH_FAILURES.pop(key, None)
    return False


def register_auth_failure(key: str):
    now = datetime.now(timezone.utc)
    record = AUTH_FAILURES.get(key) or {"count": 0, "first_seen": now, "locked_until": None}
    if record.get("first_seen") and record["first_seen"] < now - timedelta(minutes=AUTH_LOCK_MINUTES):
        record = {"count": 0, "first_seen": now, "locked_until": None}
    record["count"] = int(record.get("count") or 0) + 1
    if record["count"] >= AUTH_FAILURE_LIMIT:
        record["locked_until"] = now + timedelta(minutes=AUTH_LOCK_MINUTES)
    AUTH_FAILURES[key] = record


def clear_auth_failures(key: str):
    AUTH_FAILURES.pop(key, None)

