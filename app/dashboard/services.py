from __future__ import annotations

from datetime import datetime, timezone

from app.db import execute_sql, query_all, query_one, safe


DISTINCT_VALUE_COLUMNS = {
    "tawjihi_year",
    "tawjihi_branch",
    "university_name",
    "university_college",
    "freelancer_company",
    "freelancer_specialization",
}


def normalize_beneficiary_usage(user_id, week_start):
    row = query_one("SELECT weekly_usage_week_start FROM beneficiaries WHERE id=%s", [user_id])
    if not row:
        return
    if row["weekly_usage_week_start"] != week_start:
        execute_sql(
            """
            UPDATE beneficiaries
            SET weekly_usage_count = 0, weekly_usage_week_start = %s
            WHERE id = %s
            """,
            [week_start, user_id],
        )


def normalize_all_usage(week_start):
    execute_sql(
        """
        UPDATE beneficiaries
        SET weekly_usage_count = 0, weekly_usage_week_start = %s
        WHERE weekly_usage_week_start IS DISTINCT FROM %s
        """,
        [week_start, week_start],
    )


def get_type_label(user_type=None):
    return {
        "tawjihi": "توجيهي",
        "university": "جامعة",
        "freelancer": "فري لانسر",
    }.get(user_type, safe(user_type or ""))


def get_type_css(user_type=None):
    return {
        "tawjihi": "type-green",
        "university": "type-purple",
        "freelancer": "type-blue",
    }.get(user_type, "type-default")


def get_usage_label(row):
    count = row.get("weekly_usage_count") or 0
    limited = (
        (row.get("user_type") == "freelancer" and safe(row.get("freelancer_internet_method")) == "نظام البطاقات")
        or (row.get("user_type") == "university" and safe(row.get("university_internet_method")) == "نظام البطاقات")
    )
    return (f"{count} / 3" if limited else "غير متاح"), limited, count


def distinct_values(column, user_type=None):
    if column not in DISTINCT_VALUE_COLUMNS:
        raise ValueError(f"Unsupported distinct_values column: {column}")
    sql = f"SELECT DISTINCT {column} AS value FROM beneficiaries WHERE COALESCE({column}, '') <> ''"
    params = []
    if user_type:
        sql += " AND user_type = %s"
        params.append(user_type)
    sql += f" ORDER BY {column}"
    return [row["value"] for row in query_all(sql, params)]


def get_beneficiary_access_mode(row):
    if not row:
        return "unknown"
    if row.get("user_type") == "freelancer":
        method = safe(row.get("freelancer_internet_method"))
    elif row.get("user_type") == "university":
        method = safe(row.get("university_internet_method"))
    else:
        return "cards"
    if method in {"يوزر إنترنت", "يمتلك اسم مستخدم", "username"}:
        return "username"
    return "cards"


def get_beneficiary_access_label(row):
    return {
        "cards": "بطاقات استخدام",
        "username": "يوزر إنترنت",
        "unknown": "غير محدد",
    }.get(get_beneficiary_access_mode(row), "غير محدد")


def beneficiary_access_badge(row):
    mode = get_beneficiary_access_mode(row)
    css = "badge-purple" if mode == "cards" else "badge-green"
    return f"<span class='badge {css}'>{safe(get_beneficiary_access_label(row))}</span>"


def dashboard_live_payload(today, month_start, week_start):
    return {
        "ok": True,
        "all_count": query_one("SELECT COUNT(*) AS c FROM beneficiaries")["c"],
        "today_usage": query_one("SELECT COUNT(*) AS c FROM beneficiary_usage_logs WHERE usage_date = %s", [today])["c"],
        "month_usage": query_one("SELECT COUNT(*) AS c FROM beneficiary_usage_logs WHERE usage_date >= %s", [month_start])[
            "c"
        ],
        "archive_total": query_one("SELECT COUNT(*) AS c FROM beneficiary_usage_logs_archive")["c"],
        "active_week": query_one(
            "SELECT COUNT(DISTINCT beneficiary_id) AS c FROM beneficiary_usage_logs WHERE usage_date >= %s",
            [week_start],
        )["c"],
    }


def dashboard_page_data(today, month_start, week_start):
    live = dashboard_live_payload(today, month_start, week_start)
    stats = {
        **{key: value for key, value in live.items() if key != "ok"},
        "tawjihi_count": query_one("SELECT COUNT(*) AS c FROM beneficiaries WHERE user_type='tawjihi'")["c"],
        "university_count": query_one("SELECT COUNT(*) AS c FROM beneficiaries WHERE user_type='university'")["c"],
        "freelancer_count": query_one("SELECT COUNT(*) AS c FROM beneficiaries WHERE user_type='freelancer'")["c"],
        "accounts_count": query_one("SELECT COUNT(*) AS c FROM app_accounts")["c"],
        "active_accounts": query_one("SELECT COUNT(*) AS c FROM app_accounts WHERE is_active=TRUE")["c"],
        "card_based_count": query_one(
            """
            SELECT COUNT(*) AS c FROM beneficiaries
            WHERE (user_type='freelancer' AND freelancer_internet_method='نظام البطاقات')
               OR (user_type='university' AND university_internet_method='نظام البطاقات')
            """
        )["c"],
        "week_usage_total": query_one("SELECT COALESCE(SUM(weekly_usage_count),0) AS c FROM beneficiaries")["c"],
    }
    return {
        "stats": stats,
        "type_distribution": query_all(
            """
            SELECT
              CASE user_type
                WHEN 'tawjihi' THEN 'توجيهي'
                WHEN 'university' THEN 'جامعة'
                WHEN 'freelancer' THEN 'فري لانسر'
                ELSE user_type
              END AS label,
              COUNT(*) AS value
            FROM beneficiaries
            GROUP BY user_type
            ORDER BY value DESC
            """
        ),
        "tawjihi_by_year": query_all(
            """
            SELECT COALESCE(tawjihi_year, 'غير محدد') AS label, COUNT(*) AS value
            FROM beneficiaries
            WHERE user_type='tawjihi'
            GROUP BY COALESCE(tawjihi_year, 'غير محدد')
            ORDER BY value DESC, label
            """
        ),
        "universities_top": query_all(
            """
            SELECT COALESCE(university_name, 'غير محدد') AS label, COUNT(*) AS value
            FROM beneficiaries
            WHERE user_type='university'
            GROUP BY COALESCE(university_name, 'غير محدد')
            ORDER BY value DESC, label
            LIMIT 6
            """
        ),
        "recent_logs": query_all(
            """
            SELECT username_snapshot, action_type, target_type, details, created_at
            FROM audit_logs
            ORDER BY created_at DESC
            LIMIT 8
            """
        ),
    }


def get_power_timer_row():
    row = query_one("SELECT * FROM power_timer WHERE id=1")
    if row:
        return row
    execute_sql(
        """
        INSERT INTO power_timer (id, duration_minutes, auto_restart_delay_seconds, state, updated_by_username)
        VALUES (1, 30, 10, 'stopped', '')
        ON CONFLICT (id) DO NOTHING
        """
    )
    return query_one("SELECT * FROM power_timer WHERE id=1")


def build_power_timer_status(row=None, *, now=None):
    row = row or get_power_timer_row()
    duration_minutes = int(row.get("duration_minutes") or 30)
    duration_seconds = max(60, duration_minutes * 60)
    restart_delay = int(row.get("auto_restart_delay_seconds") or 10)
    state = row.get("state") or "stopped"
    paused_remaining = row.get("paused_remaining_seconds")
    start_at = row.get("cycle_started_at")
    now = now or datetime.now(timezone.utc)
    payload = {
        "ok": True,
        "state": state,
        "duration_minutes": duration_minutes,
        "duration_seconds": duration_seconds,
        "auto_restart_delay_seconds": restart_delay,
        "display_remaining_seconds": duration_seconds if state == "stopped" else 0,
        "phase_label": "متوقف",
        "alert_key": "",
        "updated_by_username": safe(row.get("updated_by_username")),
    }
    if state == "paused":
        remaining = max(0, int(paused_remaining or duration_seconds))
        payload.update({"display_remaining_seconds": remaining, "phase_label": "متوقف مؤقتا"})
        return payload
    if state != "running" or not start_at:
        return payload
    if isinstance(start_at, str):
        try:
            start_at = datetime.fromisoformat(start_at)
        except (TypeError, ValueError):
            return payload
    if getattr(start_at, "tzinfo", None) is None:
        start_at = start_at.replace(tzinfo=timezone.utc)
    else:
        start_at = start_at.astimezone(timezone.utc)
    elapsed = max(0, int((now - start_at).total_seconds()))
    cycle_total = duration_seconds + restart_delay
    pos = elapsed % cycle_total
    cycle_index = elapsed // cycle_total
    if pos < duration_seconds:
        remaining = duration_seconds - pos
        payload.update({"state": "running", "display_remaining_seconds": remaining, "phase_label": "العد التنازلي يعمل"})
    else:
        remaining = cycle_total - pos
        payload.update(
            {
                "state": "alarm",
                "display_remaining_seconds": remaining,
                "phase_label": "انتهى الوقت - إعادة التشغيل بعد قليل",
                "alert_key": f"{start_at.isoformat()}::{cycle_index}",
            }
        )
    return payload
