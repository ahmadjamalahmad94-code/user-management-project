# Auto-split from app/legacy.py lines 1532-1808. Loaded by app.legacy.
from app.imports.beneficiaries import (
    build_existing_lookup_maps,
    bulk_insert_beneficiaries,
    bulk_update_beneficiaries,
    infer_user_type,
    normalize_import_row,
    split_import_operations,
)


def _infer_user_type(data: dict) -> str:
    return infer_user_type(data)


def _normalize_import_row(row: dict) -> dict:
    return normalize_import_row(row, CSV_IMPORT_COLUMNS, get_week_start())


def _build_existing_lookup():
    rows = query_all("SELECT id, phone, full_name, user_type FROM beneficiaries")
    return build_existing_lookup_maps(rows)


def _bulk_insert_beneficiaries(cur, records: list[dict]):
    return bulk_insert_beneficiaries(
        cur,
        records,
        sqlite_database=is_sqlite_database_url(),
        batch_size=IMPORT_BATCH_SIZE,
    )


def _bulk_update_beneficiaries(cur, records: list[dict]):
    return bulk_update_beneficiaries(
        cur,
        records,
        sqlite_database=is_sqlite_database_url(),
        batch_size=IMPORT_BATCH_SIZE,
    )


def _process_rows_fallback(cur, task_id: str, op_name: str, batch: list[tuple[int, dict]], is_update: bool):
    ok = 0
    for row_num, data in batch:
        try:
            if is_update:
                _bulk_update_beneficiaries(cur, [data])
            else:
                _bulk_insert_beneficiaries(cur, [data])
            ok += 1
        except Exception as exc:
            cur.connection.rollback()
            append_import_log(task_id, f"Ø®Ø·Ø£ ÙÙŠ Ø§Ù„Ø³Ø·Ø± {row_num} Ø£Ø«Ù†Ø§Ø¡ {op_name}: {exc}", is_error=True)
    return ok
