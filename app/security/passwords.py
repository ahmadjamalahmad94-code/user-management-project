from __future__ import annotations

import hashlib
import hmac
import re

from werkzeug.security import check_password_hash, generate_password_hash


def clean_auth_value(value: object) -> str:
    if value is None:
        return ""
    text = str(value).strip()
    if text.lower() in {"nan", "none", "null"}:
        return ""
    return text


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def is_legacy_sha256_hash(value: str | None) -> bool:
    stored = str(value or "").strip().lower()
    return bool(re.fullmatch(r"[a-f0-9]{64}", stored))


def admin_password_hash(password: str) -> str:
    return generate_password_hash(clean_auth_value(password))


def verify_admin_password(stored_hash: str | None, password: str) -> bool:
    stored = clean_auth_value(stored_hash)
    raw = clean_auth_value(password)
    if not stored or not raw:
        return False
    if stored.startswith("pbkdf2:") or stored.startswith("scrypt:"):
        try:
            return check_password_hash(stored, raw)
        except ValueError:
            return False
    if is_legacy_sha256_hash(stored):
        return hmac.compare_digest(stored, sha256_text(raw))
    return False
