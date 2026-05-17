from __future__ import annotations

from app.db.queries import execute_sql, query_one


def _clean(value) -> str:
    return "" if value is None else str(value).strip()


def _base_username(beneficiary: dict) -> str:
    phone = _clean(beneficiary.get("phone"))
    if phone:
        return phone
    return f"BEN{int(beneficiary.get('id') or 0)}"


def _unique_username(beneficiary: dict) -> str:
    base = _base_username(beneficiary)
    current = query_one(
        """
        SELECT id FROM beneficiary_portal_accounts
        WHERE username=%s AND beneficiary_id<>%s
        LIMIT 1
        """,
        [base, beneficiary["id"]],
    )
    if not current:
        return base

    fallback = f"BEN{int(beneficiary['id'])}"
    current = query_one(
        """
        SELECT id FROM beneficiary_portal_accounts
        WHERE username=%s AND beneficiary_id<>%s
        LIMIT 1
        """,
        [fallback, beneficiary["id"]],
    )
    if not current:
        return fallback

    suffix = 2
    while True:
        candidate = f"{fallback}-{suffix}"
        current = query_one(
            """
            SELECT id FROM beneficiary_portal_accounts
            WHERE username=%s AND beneficiary_id<>%s
            LIMIT 1
            """,
            [candidate, beneficiary["id"]],
        )
        if not current:
            return candidate
        suffix += 1


def ensure_portal_account_for_beneficiary(
    beneficiary_id: int,
    *,
    is_active: bool = False,
    source: str = "system",
) -> dict:
    """Ensure every beneficiary has a portal account row.

    Inactive accounts represent "outside portal" beneficiaries. They cannot log in
    until an admin activates or resets credentials.
    """
    existing = query_one(
        "SELECT * FROM beneficiary_portal_accounts WHERE beneficiary_id=%s LIMIT 1",
        [beneficiary_id],
    )
    if existing:
        return {"created": False, "id": existing.get("id"), "username": existing.get("username")}

    beneficiary = query_one("SELECT id, phone FROM beneficiaries WHERE id=%s LIMIT 1", [beneficiary_id])
    if not beneficiary:
        return {"created": False, "id": None, "username": "", "missing": True}

    username = _unique_username(beneficiary)
    row = execute_sql(
        """
        INSERT INTO beneficiary_portal_accounts (
            beneficiary_id, username, password_hash, password_plain,
            is_active, must_set_password, activated_at
        ) VALUES (%s, %s, '', NULL, %s, TRUE, NULL)
        RETURNING id
        """,
        [beneficiary_id, username, bool(is_active)],
        fetchone=True,
    )
    return {
        "created": True,
        "id": row.get("id") if row else None,
        "username": username,
        "source": source,
    }
