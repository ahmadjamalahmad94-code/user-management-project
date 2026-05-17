# Auto-split from app/legacy.py lines 1463-1530. Loaded by app.legacy.
from app.imports.tasks import (
    append_import_log,
    configure_import_task_store,
    create_import_task,
    finalize_import_task,
    get_import_task,
    update_import_task,
)


def _now_text():
    return now_local().strftime("%Y-%m-%d %H:%M:%S")


configure_import_task_store(now_text=_now_text, log_limit=IMPORT_LOG_LIMIT)
