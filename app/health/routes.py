from __future__ import annotations

from flask import Blueprint, jsonify

from app import legacy


health_bp = Blueprint("health", __name__)


@health_bp.get("/healthz")
def healthz():
    database_ok = True
    error = ""
    try:
        legacy.query_one("SELECT 1 AS ok")
    except Exception as exc:  # pragma: no cover - exercised only on infra failure
        database_ok = False
        error = str(exc)

    status = 200 if database_ok else 503
    payload = {
        "ok": database_ok,
        "checks": {
            "app": True,
            "database": database_ok,
        },
    }
    if error:
        payload["error"] = error
    return jsonify(payload), status
