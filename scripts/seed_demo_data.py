from __future__ import annotations

import json
import os
import random
import sqlite3
from datetime import date, datetime, timedelta
from pathlib import Path

from werkzeug.security import generate_password_hash


ROOT = Path(__file__).resolve().parents[1]
DB_PATH = Path(os.getenv("HOBEHUB_LOCAL_DB_PATH", ROOT / "instance" / "hobehub_local_demo.sqlite3"))
MARKER = "DEMO_SEED"


FIRST_NAMES = [
    "أحمد",
    "محمد",
    "ليان",
    "سارة",
    "مريم",
    "نور",
    "خالد",
    "آدم",
    "جنى",
    "تالا",
    "يزن",
    "رامي",
    "هبة",
    "رنا",
    "عمر",
    "حلا",
    "محمود",
    "بيان",
    "مالك",
    "سلمى",
]
SECOND_NAMES = ["سمير", "خليل", "محمود", "حسن", "يوسف", "عادل", "سعيد", "إبراهيم", "ماهر", "نادر"]
THIRD_NAMES = ["عبدالله", "مصطفى", "علي", "أمين", "كمال", "جابر", "إسماعيل", "رائد"]
FOURTH_NAMES = ["القدسي", "الخليلي", "الرملاوي", "النجار", "الدويك", "الشامي", "الكرمي", "التميمي"]

UNIVERSITIES = ["جامعة القدس", "جامعة بيرزيت", "جامعة النجاح", "جامعة الخليل", "جامعة بوليتكنك فلسطين"]
COLLEGES = ["الهندسة", "تكنولوجيا المعلومات", "العلوم", "الأعمال", "الآداب", "الطب"]
SPECIALIZATIONS = ["علم الحاسوب", "هندسة حاسوب", "محاسبة", "تصميم جرافيك", "لغة إنجليزية", "تمريض"]
BRANCHES = ["علمي", "أدبي", "صناعي", "تجاري", "ريادة وأعمال"]
COMPANIES = ["عمل حر", "شركة محلية", "متجر إلكتروني", "مكتب هندسي", "ستوديو تصميم", "شركة ناشئة"]
FREELANCE_FIELDS = ["تصميم", "برمجة", "تسويق", "كتابة محتوى", "مونتاج", "دعم فني"]

CARD_CATEGORIES = [
    ("hour", "ساعة واحدة", 60, 10, "fa-clock", "d-badge--info"),
    ("three_hours", "ثلاث ساعات", 180, 20, "fa-stopwatch", "d-badge--success"),
    ("six_hours", "ست ساعات", 360, 30, "fa-business-time", "d-badge--warning"),
    ("day", "يوم كامل", 1440, 40, "fa-sun", "d-badge--purple"),
]


def scalar(conn: sqlite3.Connection, sql: str, params: tuple = ()) -> int:
    return int(conn.execute(sql, params).fetchone()[0] or 0)


def existing_columns(conn: sqlite3.Connection, table: str) -> set[str]:
    return {row[1] for row in conn.execute(f"PRAGMA table_info({table})")}


def insert_row(conn: sqlite3.Connection, table: str, data: dict) -> int:
    cols = [key for key in data if key in existing_columns(conn, table)]
    placeholders = ", ".join("?" for _ in cols)
    sql = f"INSERT INTO {table} ({', '.join(cols)}) VALUES ({placeholders})"
    cur = conn.execute(sql, [data[key] for key in cols])
    return int(cur.lastrowid)


def cleanup_previous_seed(conn: sqlite3.Connection) -> None:
    seeded_ids = [
        row[0]
        for row in conn.execute(
            "SELECT id FROM beneficiaries WHERE notes LIKE ? OR phone LIKE '0598%'",
            (f"{MARKER}:%",),
        )
    ]
    if seeded_ids:
        placeholders = ", ".join("?" for _ in seeded_ids)
        for table in [
            "beneficiary_group_members",
            "beneficiary_portal_accounts",
            "beneficiary_radius_accounts",
            "beneficiary_issued_cards",
            "beneficiary_usage_logs",
            "internet_service_requests",
            "temporary_speed_upgrades",
            "radius_pending_actions",
        ]:
            if table in table_names(conn):
                conn.execute(f"DELETE FROM {table} WHERE beneficiary_id IN ({placeholders})", seeded_ids)
        conn.execute(f"DELETE FROM beneficiaries WHERE id IN ({placeholders})", seeded_ids)

    if "manual_access_cards" in table_names(conn):
        conn.execute("DELETE FROM manual_access_cards WHERE source_file = ?", (MARKER,))
    if "beneficiary_groups" in table_names(conn):
        conn.execute("DELETE FROM beneficiary_groups WHERE name LIKE ?", (f"{MARKER} - %",))
    if "card_quota_policies" in table_names(conn):
        conn.execute("DELETE FROM card_quota_policies WHERE notes LIKE ?", (f"{MARKER}:%",))
    if "radius_pending_actions" in table_names(conn):
        conn.execute("DELETE FROM radius_pending_actions WHERE notes LIKE ?", (f"{MARKER}:%",))
    if "audit_logs" in table_names(conn):
        conn.execute("DELETE FROM audit_logs WHERE details LIKE ?", (f"{MARKER}:%",))


def table_names(conn: sqlite3.Connection) -> set[str]:
    return {row[0] for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}


def ensure_categories(conn: sqlite3.Connection) -> None:
    if "card_categories" not in table_names(conn):
        return
    for code, label, minutes, order, icon, color in CARD_CATEGORIES:
        conn.execute(
            """
            INSERT INTO card_categories
                (code, label_ar, duration_minutes, display_order, is_active, icon, color_class, notes)
            VALUES (?, ?, ?, ?, 1, ?, ?, ?)
            ON CONFLICT(code) DO UPDATE SET
                label_ar=excluded.label_ar,
                duration_minutes=excluded.duration_minutes,
                display_order=excluded.display_order,
                is_active=1,
                icon=excluded.icon,
                color_class=excluded.color_class,
                notes=excluded.notes,
                updated_at=CURRENT_TIMESTAMP
            """,
            (code, label, minutes, order, icon, color, f"{MARKER}: demo category"),
        )


def full_name(index: int) -> tuple[str, str, str, str, str]:
    first = FIRST_NAMES[index % len(FIRST_NAMES)]
    second = SECOND_NAMES[(index * 3) % len(SECOND_NAMES)]
    third = THIRD_NAMES[(index * 5) % len(THIRD_NAMES)]
    fourth = FOURTH_NAMES[(index * 7) % len(FOURTH_NAMES)]
    return first, second, third, fourth, f"{first} {second} {third} {fourth}"


def create_beneficiaries(conn: sqlite3.Connection) -> list[dict]:
    today = date.today()
    week_start = today - timedelta(days=today.weekday())
    beneficiaries: list[dict] = []
    total = 96
    for idx in range(total):
        if idx < 32:
            user_type = "tawjihi"
        elif idx < 68:
            user_type = "university"
        else:
            user_type = "freelancer"

        first, second, third, fourth, name = full_name(idx)
        phone = f"0598{idx:06d}"
        access_is_username = user_type in {"university", "freelancer"} and idx % 3 != 0
        internet_method = "يوزر إنترنت" if access_is_username else "نظام البطاقات"
        created_at = datetime.now() - timedelta(days=random.randint(0, 120), hours=random.randint(0, 12))
        data = {
            "user_type": user_type,
            "first_name": first,
            "second_name": second,
            "third_name": third,
            "fourth_name": fourth,
            "full_name": name,
            "search_name": name.replace("أ", "ا").replace("إ", "ا").replace("آ", "ا"),
            "phone": phone,
            "weekly_usage_count": random.randint(0, 3),
            "weekly_usage_week_start": week_start.isoformat(),
            "notes": f"{MARKER}: بيانات معاينة كثيفة",
            "added_by_account_id": 1,
            "added_by_username": "admin",
            "created_at": created_at.strftime("%Y-%m-%d %H:%M:%S"),
        }

        if user_type == "tawjihi":
            data.update(
                {
                    "tawjihi_year": str(random.choice([2024, 2025, 2026])),
                    "tawjihi_branch": random.choice(BRANCHES),
                }
            )
        elif user_type == "university":
            data.update(
                {
                    "university_name": random.choice(UNIVERSITIES),
                    "university_number": f"U-{2026}-{idx:04d}",
                    "university_college": random.choice(COLLEGES),
                    "university_specialization": random.choice(SPECIALIZATIONS),
                    "university_days": random.choice(["الأحد، الثلاثاء، الخميس", "الاثنين، الأربعاء", "كل أيام الأسبوع"]),
                    "university_internet_method": internet_method,
                    "university_time_mode": random.choice(["دوام كامل", "جزئي", "مسائي"]),
                    "university_time_from": random.choice(["08:00", "09:00", "10:00"]),
                    "university_time_to": random.choice(["14:00", "15:00", "16:00"]),
                }
            )
        else:
            data.update(
                {
                    "freelancer_specialization": random.choice(FREELANCE_FIELDS),
                    "freelancer_company": random.choice(COMPANIES),
                    "freelancer_schedule_type": random.choice(["ثابت", "مرن", "حسب الطلب"]),
                    "freelancer_internet_method": internet_method,
                    "freelancer_time_mode": random.choice(["صباحي", "مسائي", "مفتوح"]),
                    "freelancer_time_from": random.choice(["09:00", "12:00", "17:00"]),
                    "freelancer_time_to": random.choice(["15:00", "18:00", "22:00"]),
                    "freelancer_type": random.choice(["مستقل", "شركة", "طالب عامل"]),
                    "freelancer_field": random.choice(FREELANCE_FIELDS),
                    "company_name": random.choice(COMPANIES),
                    "company_proof": random.choice(["هوية عمل", "رابط أعمال", "تعريف شركة", ""]),
                }
            )

        beneficiary_id = insert_row(conn, "beneficiaries", data)
        beneficiaries.append(
            {
                "id": beneficiary_id,
                "name": name,
                "phone": phone,
                "user_type": user_type,
                "access_mode": "username" if access_is_username else "cards",
            }
        )
    return beneficiaries


def create_portal_and_radius_accounts(conn: sqlite3.Connection, beneficiaries: list[dict]) -> None:
    for item in beneficiaries:
        if item["access_mode"] != "username":
            continue
        username = f"user{item['id']:04d}"
        password = "demo12345"
        insert_row(
            conn,
            "beneficiary_portal_accounts",
            {
                "beneficiary_id": item["id"],
                "username": username,
                "password_hash": generate_password_hash(password),
                "is_active": 1,
                "must_set_password": 0,
                "activated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "last_login_at": (datetime.now() - timedelta(days=random.randint(0, 20))).strftime("%Y-%m-%d %H:%M:%S"),
            },
        )
        insert_row(
            conn,
            "beneficiary_radius_accounts",
            {
                "beneficiary_id": item["id"],
                "external_user_id": f"rad-{item['id']}",
                "external_username": username,
                "current_profile_id": random.choice(["p1", "p2", "p3", "p4"]),
                "current_profile_name": random.choice(["5M مجاني", "10M طالب", "15M عمل", "20M VIP"]),
                "original_profile_id": "p1",
                "status": random.choice(["active", "active", "pending", "suspended"]),
                "plain_password": password,
                "mac_address": f"AA:BB:CC:{item['id'] % 255:02X}:{(item['id'] * 2) % 255:02X}:{(item['id'] * 3) % 255:02X}",
                "data_quota_mb_total": random.choice([2048, 5120, 10240, 20480]),
                "data_quota_mb_used": random.randint(100, 9000),
                "time_quota_minutes_total": random.choice([300, 600, 1200, 2400]),
                "time_quota_minutes_used": random.randint(20, 800),
                "last_sync_at": (datetime.now() - timedelta(hours=random.randint(1, 72))).strftime("%Y-%m-%d %H:%M:%S"),
                "sync_status": random.choice(["synced", "pending", "manual"]),
                "notes": f"{MARKER}: حساب RADIUS وهمي",
            },
        )


def create_cards(conn: sqlite3.Connection, beneficiaries: list[dict]) -> None:
    card_mode_users = [item for item in beneficiaries if item["access_mode"] == "cards"]
    durations = [60, 180, 360, 1440]
    for duration in durations:
        for n in range(70):
            insert_row(
                conn,
                "manual_access_cards",
                {
                    "duration_minutes": duration,
                    "card_username": f"DEMO{duration}{n:04d}",
                    "card_password": f"{duration}{random.randint(100000, 999999)}",
                    "source_file": MARKER,
                    "imported_by_username": "admin",
                    "created_at": (datetime.now() - timedelta(days=random.randint(0, 15))).strftime("%Y-%m-%d %H:%M:%S"),
                },
            )

    for n in range(90):
        user = random.choice(card_mode_users)
        issued_at = datetime.now() - timedelta(days=random.randint(0, 21), hours=random.randint(0, 20))
        insert_row(
            conn,
            "beneficiary_issued_cards",
            {
                "beneficiary_id": user["id"],
                "duration_minutes": random.choice(durations),
                "card_username": f"USED{user['id']}{n:04d}",
                "card_password": f"P{random.randint(100000, 999999)}",
                "issued_by": random.choice(["admin", "system", "manual-demo"]),
                "router_login_url_snapshot": "http://hotspot.local/login",
                "issued_at": issued_at.strftime("%Y-%m-%d %H:%M:%S"),
            },
        )


def create_groups_and_policies(conn: sqlite3.Connection, beneficiaries: list[dict]) -> None:
    group_defs = [
        ("طلاب جامعات - صباحي", "طلاب يملكون حضور صباحي وحد بطاقة يومي"),
        ("مشتركو البطاقات VIP", "مرونة أعلى في البطاقات"),
        ("فريلانسر مسائي", "مشتركين يعملون بعد الظهر"),
        ("تجربة تحويل يوزر/بطاقة", "مجموعة للمعاينة والتحويل"),
    ]
    groups = []
    for idx, (name, desc) in enumerate(group_defs):
        group_id = insert_row(
            conn,
            "beneficiary_groups",
            {
                "name": f"{MARKER} - {name}",
                "description": desc,
                "color_class": random.choice(["d-badge--info", "d-badge--success", "d-badge--warning", "d-badge--purple"]),
                "is_active": 1,
                "created_by_account_id": 1,
            },
        )
        groups.append(group_id)
        for user in beneficiaries[idx * 8 : idx * 8 + 18]:
            insert_row(conn, "beneficiary_group_members", {"group_id": group_id, "beneficiary_id": user["id"]})

    policies = [
        ("default", None, 1, 3, "", "hour,three_hours", 100, "افتراضي: بطاقة يوميا وثلاث أسبوعيا"),
        ("group", groups[0], 2, 4, "0,2,4", "hour,three_hours", 50, "طلاب صباحي: الأحد الثلاثاء الخميس"),
        ("group", groups[1], 3, 8, "", "hour,three_hours,six_hours,day", 40, "VIP: مرونة أعلى"),
        ("group", groups[2], 1, 5, "1,3,5", "three_hours,six_hours", 60, "فريلانسر مسائي"),
        ("user", beneficiaries[5]["id"], 2, 2, "", "day", 10, "تخصيص فردي: يوم كامل مرتين فقط"),
    ]
    for scope, target_id, daily, weekly, days, cats, priority, notes in policies:
        insert_row(
            conn,
            "card_quota_policies",
            {
                "scope": scope,
                "target_id": target_id,
                "daily_limit": daily,
                "weekly_limit": weekly,
                "allowed_days": days,
                "allowed_category_codes": cats,
                "priority": priority,
                "is_active": 1,
                "notes": f"{MARKER}: {notes}",
                "created_by_account_id": 1,
            },
        )


def create_requests_and_logs(conn: sqlite3.Connection, beneficiaries: list[dict]) -> None:
    request_types = ["speed_upgrade", "password_reset", "open_blocked_site", "change_mac", "connection_issue", "extra_card"]
    statuses = ["pending", "pending", "approved", "rejected", "executed"]
    for n in range(75):
        user = random.choice(beneficiaries)
        req_type = random.choice(request_types)
        status = random.choice(statuses)
        created_at = datetime.now() - timedelta(days=random.randint(0, 30), hours=random.randint(0, 23))
        reviewed_at = created_at + timedelta(hours=random.randint(2, 36)) if status != "pending" else None
        payload = {
            "reason": random.choice(["للدراسة", "اجتماع عمل", "مشكلة اتصال", "حاجة مؤقتة", "اختبار خدمة"]),
            "requested_speed": random.choice(["10M", "15M", "20M", ""]),
            "site": random.choice(["github.com", "zoom.us", "figma.com", "docs.google.com", ""]),
        }
        insert_row(
            conn,
            "internet_service_requests",
            {
                "beneficiary_id": user["id"],
                "request_type": req_type,
                "status": status,
                "requested_payload": json.dumps(payload, ensure_ascii=False),
                "admin_payload": json.dumps({"note": "بيانات معاينة"}, ensure_ascii=False),
                "api_endpoint": "/app_ad/demo" if status == "executed" else "",
                "api_response": json.dumps({"error": False, "demo": True}, ensure_ascii=False) if status == "executed" else "{}",
                "error_message": "" if status != "rejected" else "مرفوض للمعاينة فقط",
                "requested_by": "beneficiary",
                "reviewed_by": "admin" if reviewed_at else "",
                "reviewed_at": reviewed_at.strftime("%Y-%m-%d %H:%M:%S") if reviewed_at else None,
                "executed_at": reviewed_at.strftime("%Y-%m-%d %H:%M:%S") if status == "executed" and reviewed_at else None,
                "created_at": created_at.strftime("%Y-%m-%d %H:%M:%S"),
                "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            },
        )

    for n in range(160):
        user = random.choice(beneficiaries)
        at = datetime.now() - timedelta(days=random.randint(0, 45), hours=random.randint(0, 23))
        insert_row(
            conn,
            "beneficiary_usage_logs",
            {
                "beneficiary_id": user["id"],
                "usage_reason": random.choice(["بطاقة يومية", "دراسة", "عمل", "طلب استثنائي", "تجربة"]),
                "card_type": random.choice(["ساعة", "ثلاث ساعات", "ست ساعات", "يوم كامل"]),
                "usage_date": at.date().isoformat(),
                "usage_time": at.strftime("%Y-%m-%d %H:%M:%S"),
                "notes": f"{MARKER}: سجل استخدام وهمي",
                "added_by_account_id": 1,
                "added_by_username": "admin",
            },
        )

    for n in range(100):
        user = random.choice(beneficiaries)
        at = datetime.now() - timedelta(days=random.randint(0, 60), minutes=random.randint(0, 500))
        insert_row(
            conn,
            "audit_logs",
            {
                "account_id": 1,
                "username_snapshot": random.choice(["admin", "system", "operator"]),
                "action_type": random.choice(["create", "update", "approve", "issue_card", "convert_access", "sync_radius"]),
                "target_type": random.choice(["beneficiary", "card", "request", "radius"]),
                "target_id": user["id"],
                "details": f"{MARKER}: عملية معاينة على {user['name']}",
                "created_at": at.strftime("%Y-%m-%d %H:%M:%S"),
            },
        )

    username_users = [item for item in beneficiaries if item["access_mode"] == "username"]
    for n in range(22):
        user = random.choice(username_users)
        status = random.choice(["pending", "pending", "done", "failed"])
        insert_row(
            conn,
            "radius_pending_actions",
            {
                "action_type": random.choice(["change_profile", "reset_password", "disconnect_user", "add_quota"]),
                "target_kind": "user",
                "target_external_id": f"rad-{user['id']}",
                "beneficiary_id": user["id"],
                "payload_json": json.dumps({"demo": True, "profile": random.choice(["10M", "15M", "20M"])}, ensure_ascii=False),
                "status": status,
                "attempted_by_mode": random.choice(["manual", "live"]),
                "api_endpoint": "/app_ad/demo_action",
                "api_response_json": json.dumps({"error": status == "failed"}, ensure_ascii=False),
                "error_message": "فشل وهمي للمعاينة" if status == "failed" else "",
                "notes": f"{MARKER}: إجراء RADIUS وهمي",
                "requested_by_account_id": 1,
                "requested_by_username": "admin",
            },
        )


def main() -> None:
    if not DB_PATH.exists():
        raise SystemExit(f"Database not found: {DB_PATH}")
    random.seed(20260516)
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        with conn:
            cleanup_previous_seed(conn)
            ensure_categories(conn)
            beneficiaries = create_beneficiaries(conn)
            create_portal_and_radius_accounts(conn, beneficiaries)
            create_cards(conn, beneficiaries)
            create_groups_and_policies(conn, beneficiaries)
            create_requests_and_logs(conn, beneficiaries)
        with conn:
            create_requests_and_logs(conn, beneficiaries)

        summary = {
            "database": str(DB_PATH),
            "beneficiaries": scalar(conn, "SELECT COUNT(*) FROM beneficiaries WHERE notes LIKE ?", (f"{MARKER}:%",)),
            "portal_accounts": scalar(
                conn,
                """
                SELECT COUNT(*) FROM beneficiary_portal_accounts
                WHERE beneficiary_id IN (SELECT id FROM beneficiaries WHERE notes LIKE ?)
                """,
                (f"{MARKER}:%",),
            ),
            "manual_cards": scalar(conn, "SELECT COUNT(*) FROM manual_access_cards WHERE source_file=?", (MARKER,)),
            "issued_cards": scalar(
                conn,
                """
                SELECT COUNT(*) FROM beneficiary_issued_cards
                WHERE beneficiary_id IN (SELECT id FROM beneficiaries WHERE notes LIKE ?)
                """,
                (f"{MARKER}:%",),
            ),
            "requests": scalar(
                conn,
                """
                SELECT COUNT(*) FROM internet_service_requests
                WHERE beneficiary_id IN (SELECT id FROM beneficiaries WHERE notes LIKE ?)
                """,
                (f"{MARKER}:%",),
            ),
            "usage_logs": scalar(
                conn,
                """
                SELECT COUNT(*) FROM beneficiary_usage_logs
                WHERE beneficiary_id IN (SELECT id FROM beneficiaries WHERE notes LIKE ?)
                """,
                (f"{MARKER}:%",),
            ),
        }
        print(json.dumps(summary, ensure_ascii=False, indent=2))
    finally:
        conn.close()


if __name__ == "__main__":
    main()
