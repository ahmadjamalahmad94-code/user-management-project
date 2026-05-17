# Auto-split from app/legacy.py lines 6810-6900. Loaded by app.legacy.
INTERNET_REQUEST_TYPE_LABELS = {
    "create_user": "طلب خدمة إنترنت",
    "request_card": "طلب بطاقة استخدام",
    "extra_card": "طلب بطاقة إضافية",
    "temporary_speed_upgrade": "طلب رفع سرعة مؤقت",
    "speed_upgrade": "طلب رفع السرعة",
    "add_time": "طلب إضافة وقت",
    "add_quota": "طلب إضافة رصيد بيانات",
    "add_quota_mb": "طلب إضافة رصيد بيانات",
    "update_mac": "طلب تغيير عنوان الجهاز",
    "change_mac": "طلب تغيير عنوان الجهاز",
    "reset_password": "طلب إعادة تعيين كلمة المرور",
    "password_reset": "طلب إعادة تعيين كلمة المرور",
    "connection_issue": "بلاغ مشكلة اتصال",
    "open_blocked_site": "طلب فتح موقع محجوب",
    "unblock_site": "طلب فتح موقع محجوب",
    "other": "طلب آخر",
}

INTERNET_REQUEST_STATUS_LABELS = {
    "pending": "قيد المراجعة",
    "approved": "تمت الموافقة",
    "rejected": "مرفوض",
    "executed": "تم التنفيذ",
    "failed": "فشل التنفيذ",
    "cancelled": "ملغي",
}


def internet_request_type_label(value: str | None) -> str:
    return INTERNET_REQUEST_TYPE_LABELS.get(clean_csv_value(value), clean_csv_value(value) or "-")


def internet_request_status_label(value: str | None) -> str:
    return INTERNET_REQUEST_STATUS_LABELS.get(clean_csv_value(value), clean_csv_value(value) or "-")


def internet_request_status_pill(value: str | None) -> str:
    status = clean_csv_value(value) or "pending"
    css = {
        "pending": "pill orange",
        "approved": "pill green",
        "rejected": "pill red",
        "executed": "pill green",
        "failed": "pill red",
        "cancelled": "pill",
    }.get(status, "pill")
    return f"<span class='{css}'>{safe(internet_request_status_label(status))}</span>"


def internet_request_type_badge(value: str | None) -> str:
    request_type = clean_csv_value(value) or "other"
    css = {
        "create_user": "request-type-badge type-blue",
        "request_card": "request-type-badge type-orange",
        "temporary_speed_upgrade": "request-type-badge type-purple",
        "add_time": "request-type-badge type-green",
        "add_quota": "request-type-badge type-cyan",
        "update_mac": "request-type-badge type-slate",
        "reset_password": "request-type-badge type-red",
        "other": "request-type-badge",
    }.get(request_type, "request-type-badge")
    return f"<span class='{css}'>{safe(internet_request_type_label(request_type))}</span>"


def json_safe_dict(value) -> dict:
    if isinstance(value, dict):
        return value
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
            return parsed if isinstance(parsed, dict) else {}
        except json.JSONDecodeError:
            return {}
    return {}


def request_payload_summary(data: dict) -> str:
    if not data:
        return "-"
    parts = []
    keys = [
        "external_username",
        "desired_username",
        "profile_name",
        "profile_id",
        "duration_minutes",
        "time_amount",
        "quota_amount_mb",
        "card_count",
        "mac_address",
    ]
    for key in keys:
        val = clean_csv_value(data.get(key))
        if val:
            parts.append(f"{key}: {val}")
    if not parts:
        parts = [f"{k}: {safe(v)}" for k, v in list(data.items())[:4] if safe(v)]
    return "<br>".join(parts[:6]) if parts else "-"
