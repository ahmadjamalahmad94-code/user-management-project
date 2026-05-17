# Auto-split from app/legacy.py lines 2038-2243. Loaded by app.legacy.
def card_duration_label(duration_minutes):
    try:
        minutes = int(duration_minutes or 0)
    except Exception:
        minutes = 0
    for item in CARD_DURATION_OPTIONS:
        if item["minutes"] == minutes:
            return item["label"]
    return f"{minutes} دقيقة" if minutes else "غير محدد"


def get_router_login_url():
    from app.services.mikrotik_hotspot import hotspot_login_url

    row = get_radius_settings_row() or {}
    return clean_csv_value(row.get("router_login_url")) or hotspot_login_url()


def parse_manual_cards_upload(file_storage, filename_hint=""):
    filename = clean_csv_value(getattr(file_storage, "filename", "")) or filename_hint
    ext = os.path.splitext(filename.lower())[1]
    cards = []
    if ext == ".csv":
        stream = io.StringIO(file_storage.stream.read().decode("utf-8-sig"))
        reader = csv.reader(stream)
        rows = list(reader)
    elif ext in {".xlsx", ".xlsm", ".xltx", ".xltm"}:
        workbook = load_workbook(file_storage, read_only=True, data_only=True)
        ws = workbook.active
        rows = list(ws.iter_rows(values_only=True))
    else:
        raise ValueError("صيغة الملف غير مدعومة. استخدم CSV أو XLSX.")

    for raw in rows:
        if not raw:
            continue
        cells = [clean_csv_value(x) for x in raw]
        cells = [c for c in cells if c]
        if len(cells) < 2:
            continue
        username, password = cells[0], cells[1]
        if username.lower() in {"username", "user", "card", "login"}:
            continue
        if password.lower() in {"password", "pass"}:
            continue
        cards.append({"card_username": username, "card_password": password})
    if not cards:
        raise ValueError("لم يتم العثور على بطاقات صالحة داخل الملف.")
    return cards


def import_manual_access_cards(duration_minutes: int, file_storage, source_name: str, imported_by_username: str):
    cards = parse_manual_cards_upload(file_storage, source_name)
    seen_usernames = set()
    duplicate_in_file = []
    normalized_cards = []
    for card in cards:
        username = clean_csv_value(card["card_username"])
        password = clean_csv_value(card["card_password"])
        username_key = username.strip().lower()
        if not username or not password:
            continue
        if username_key in seen_usernames:
            duplicate_in_file.append(username)
        seen_usernames.add(username_key)
        normalized_cards.append({"card_username": username, "card_password": password})

    if duplicate_in_file:
        sample = ", ".join(duplicate_in_file[:5])
        raise ValueError(f"الملف يحتوي بطاقات مكررة بنفس اسم البطاقة: {sample}")

    if not normalized_cards:
        raise ValueError("لم يتم العثور على بطاقات صالحة داخل الملف.")

    username_keys = [card["card_username"].strip().lower() for card in normalized_cards]
    placeholders = ",".join(["%s"] * len(username_keys))
    normalize_expr = "LOWER(TRIM(card_username))" if is_sqlite_database_url() else "LOWER(BTRIM(card_username))"
    existing_inventory = query_all(
        f"""
        SELECT card_username
        FROM manual_access_cards
        WHERE {normalize_expr} IN ({placeholders})
        LIMIT 10
        """,
        username_keys,
    )
    existing_issued = query_all(
        f"""
        SELECT card_username
        FROM beneficiary_issued_cards
        WHERE {normalize_expr} IN ({placeholders})
        LIMIT 10
        """,
        username_keys,
    )
    existing_names = sorted(
        {
            clean_csv_value(row.get("card_username"))
            for row in [*existing_inventory, *existing_issued]
            if row.get("card_username")
        }
    )
    if existing_names:
        sample = ", ".join(existing_names[:5])
        raise ValueError(f"يوجد بطاقات مكررة مسبقاً بنفس اسم البطاقة، تم إيقاف الاستيراد: {sample}")

    inserted = 0
    for card in normalized_cards:
        execute_sql(
            """
            INSERT INTO manual_access_cards (
                duration_minutes, card_username, card_password, source_file, imported_by_username
            ) VALUES (%s,%s,%s,%s,%s)
            """,
            [
                duration_minutes,
                card["card_username"],
                card["card_password"],
                source_name,
                imported_by_username,
            ],
        )
        inserted += 1
    return inserted


def get_manual_cards_inventory_counts():
    rows = query_all(
        """
        SELECT duration_minutes, COUNT(*) AS c
        FROM manual_access_cards
        GROUP BY duration_minutes
        ORDER BY duration_minutes ASC
        """
    )
    counts = {int(r["duration_minutes"]): int(r["c"]) for r in rows}
    return [{"minutes": item["minutes"], "label": item["label"], "available": counts.get(item["minutes"], 0)} for item in CARD_DURATION_OPTIONS]


def get_latest_issued_card_for_beneficiary(beneficiary_id: int):
    return query_one(
        """
        SELECT * FROM beneficiary_issued_cards
        WHERE beneficiary_id=%s
        ORDER BY id DESC
        LIMIT 1
        """,
        [beneficiary_id],
    )


def count_beneficiary_card_requests_today(beneficiary_id: int):
    row = query_one(
        "SELECT COUNT(*) AS c FROM beneficiary_usage_logs WHERE beneficiary_id=%s AND usage_date=%s",
        [beneficiary_id, today_local()],
    )
    return int((row or {}).get("c") or 0)


def count_beneficiary_card_requests_week(beneficiary_id: int):
    row = query_one(
        "SELECT COUNT(*) AS c FROM beneficiary_usage_logs WHERE beneficiary_id=%s AND usage_date >= %s",
        [beneficiary_id, get_week_start()],
    )
    return int((row or {}).get("c") or 0)


def validate_beneficiary_card_request(beneficiary_id: int, duration_minutes: int):
    daily_count = count_beneficiary_card_requests_today(beneficiary_id)
    if daily_count >= 1:
        return False, "يمكن طلب بطاقة واحدة فقط في اليوم."
    weekly_count = count_beneficiary_card_requests_week(beneficiary_id)
    if weekly_count >= 3:
        return False, "تم الوصول إلى الحد الأقصى الأسبوعي لطلبات البطاقات."
    available = query_one(
        "SELECT COUNT(*) AS c FROM manual_access_cards WHERE duration_minutes=%s",
        [duration_minutes],
    )
    if int((available or {}).get("c") or 0) <= 0:
        return False, f"لا توجد بطاقات متاحة حاليًا لمدة {card_duration_label(duration_minutes)}."
    return True, ""
