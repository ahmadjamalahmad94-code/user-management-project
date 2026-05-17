from __future__ import annotations

from psycopg2.extras import execute_batch, execute_values

from app.utils.text import clean_csv_value, full_name_from_parts, normalize_phone, normalize_search_ar


BENEFICIARY_IMPORT_COLUMNS = (
    "user_type",
    "first_name",
    "second_name",
    "third_name",
    "fourth_name",
    "full_name",
    "search_name",
    "phone",
    "tawjihi_year",
    "tawjihi_branch",
    "freelancer_specialization",
    "freelancer_company",
    "freelancer_schedule_type",
    "freelancer_internet_method",
    "freelancer_time_mode",
    "freelancer_time_from",
    "freelancer_time_to",
    "university_name",
    "university_number",
    "university_college",
    "university_specialization",
    "university_days",
    "university_internet_method",
    "university_time_mode",
    "university_time_from",
    "university_time_to",
    "weekly_usage_count",
    "weekly_usage_week_start",
    "notes",
    "added_by_account_id",
    "added_by_username",
)


def infer_user_type(data: dict) -> str:
    if data.get("user_type"):
        return data["user_type"]
    if data.get("tawjihi_year") or data.get("tawjihi_branch"):
        return "tawjihi"
    if data.get("university_name") or data.get("university_specialization"):
        return "university"
    return "freelancer"


def normalize_import_row(row: dict, csv_columns, week_start) -> dict:
    data = {column: clean_csv_value(row.get(column, "")) for column in csv_columns}
    data["phone"] = normalize_phone(data["phone"])
    data["full_name"] = full_name_from_parts(
        data["first_name"],
        data["second_name"],
        data["third_name"],
        data["fourth_name"],
    )
    data["search_name"] = normalize_search_ar(data["full_name"])
    data["user_type"] = infer_user_type(data)
    data["weekly_usage_week_start"] = week_start
    return data


def build_existing_lookup_maps(rows):
    phone_map = {}
    name_type_map = {}
    for row in rows:
        phone = clean_csv_value(row.get("phone"))
        if phone and phone not in phone_map:
            phone_map[phone] = row["id"]
        key = (clean_csv_value(row.get("full_name")), clean_csv_value(row.get("user_type")))
        if key[0] and key not in name_type_map:
            name_type_map[key] = row["id"]
    return phone_map, name_type_map


def split_import_operations(normalized_rows, phone_map, name_type_map):
    inserts = []
    updates = []
    for row_num, data in normalized_rows:
        existing_id = None
        if data.get("phone"):
            existing_id = phone_map.get(data["phone"])
        if not existing_id:
            existing_id = name_type_map.get((data["full_name"], data["user_type"]))
        if existing_id:
            data["id"] = existing_id
            updates.append((row_num, data))
        else:
            inserts.append((row_num, data))
            if data.get("phone"):
                phone_map[data["phone"]] = -1
            name_type_map[(data["full_name"], data["user_type"])] = -1
    return inserts, updates


def _insert_values(records: list[dict]):
    return [
        (
            data["user_type"],
            data["first_name"],
            data["second_name"],
            data["third_name"],
            data["fourth_name"],
            data["full_name"],
            data["search_name"],
            data["phone"],
            data["tawjihi_year"],
            data["tawjihi_branch"],
            data["freelancer_specialization"],
            data["freelancer_company"],
            data["freelancer_schedule_type"],
            data["freelancer_internet_method"],
            data["freelancer_time_mode"],
            data["freelancer_time_from"],
            data["freelancer_time_to"],
            data["university_name"],
            data["university_number"],
            data["university_college"],
            data["university_specialization"],
            data["university_days"],
            data["university_internet_method"],
            data["university_time_mode"],
            data["university_time_from"],
            data["university_time_to"],
            0,
            data["weekly_usage_week_start"],
            data.get("notes", ""),
            data.get("added_by_account_id"),
            data.get("added_by_username", ""),
        )
        for data in records
    ]


def bulk_insert_beneficiaries(cur, records: list[dict], *, sqlite_database: bool, batch_size: int):
    if not records:
        return
    values = _insert_values(records)
    if sqlite_database:
        sql = """
            INSERT INTO beneficiaries (
                user_type, first_name, second_name, third_name, fourth_name,
                full_name, search_name, phone, tawjihi_year, tawjihi_branch,
                freelancer_specialization, freelancer_company, freelancer_schedule_type,
                freelancer_internet_method, freelancer_time_mode, freelancer_time_from,
                freelancer_time_to, university_name, university_number, university_college, university_specialization,
                university_days, university_internet_method, university_time_mode,
                university_time_from, university_time_to, weekly_usage_count, weekly_usage_week_start,
                notes, added_by_account_id, added_by_username
            ) VALUES (
                %s,%s,%s,%s,%s,%s,%s,%s,%s,%s,
                %s,%s,%s,%s,%s,%s,%s,%s,%s,%s,
                %s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s
            )
        """
        cur.executemany(sql, values)
        return

    sql = """
        INSERT INTO beneficiaries (
            user_type, first_name, second_name, third_name, fourth_name,
            full_name, search_name, phone, tawjihi_year, tawjihi_branch,
            freelancer_specialization, freelancer_company, freelancer_schedule_type,
            freelancer_internet_method, freelancer_time_mode, freelancer_time_from,
            freelancer_time_to, university_name, university_number, university_college, university_specialization,
            university_days, university_internet_method, university_time_mode,
            university_time_from, university_time_to, weekly_usage_count, weekly_usage_week_start,
            notes, added_by_account_id, added_by_username
        ) VALUES %s
    """
    execute_values(cur, sql, values, page_size=min(batch_size, 500))


def bulk_update_beneficiaries(cur, records: list[dict], *, sqlite_database: bool, batch_size: int):
    if not records:
        return
    sql = """
        UPDATE beneficiaries SET
            user_type=%s, first_name=%s, second_name=%s, third_name=%s, fourth_name=%s,
            full_name=%s, search_name=%s, phone=%s, tawjihi_year=%s, tawjihi_branch=%s,
            freelancer_specialization=%s, freelancer_company=%s, freelancer_schedule_type=%s,
            freelancer_internet_method=%s, freelancer_time_mode=%s, freelancer_time_from=%s,
            freelancer_time_to=%s, university_name=%s, university_number=%s, university_college=%s,
            university_specialization=%s, university_days=%s, university_internet_method=%s,
            university_time_mode=%s, university_time_from=%s, university_time_to=%s,
            notes=%s
        WHERE id=%s
    """
    params = [
        (
            data["user_type"],
            data["first_name"],
            data["second_name"],
            data["third_name"],
            data["fourth_name"],
            data["full_name"],
            data["search_name"],
            data["phone"],
            data["tawjihi_year"],
            data["tawjihi_branch"],
            data["freelancer_specialization"],
            data["freelancer_company"],
            data["freelancer_schedule_type"],
            data["freelancer_internet_method"],
            data["freelancer_time_mode"],
            data["freelancer_time_from"],
            data["freelancer_time_to"],
            data["university_name"],
            data["university_number"],
            data["university_college"],
            data["university_specialization"],
            data["university_days"],
            data["university_internet_method"],
            data["university_time_mode"],
            data["university_time_from"],
            data["university_time_to"],
            data.get("notes", ""),
            data["id"],
        )
        for data in records
    ]
    if sqlite_database:
        cur.executemany(sql, params)
    else:
        execute_batch(cur, sql, params, page_size=min(batch_size, 500))
