from app import legacy


archive_usage_logs = legacy.archive_usage_logs
archive_usage_logs_before = legacy.archive_usage_logs_before
clear_usage_logs = legacy.clear_usage_logs
clear_usage_logs_before = legacy.clear_usage_logs_before
usage_archive_page = legacy.usage_archive_page
export_archive_excel = legacy.export_archive_excel
restore_archive_logs = legacy.restore_archive_logs
restore_archive_logs_before = legacy.restore_archive_logs_before
clear_archive_logs = legacy.clear_archive_logs

ROUTES = [
    ("POST", "/usage-logs/archive", "archive_usage_logs"),
    ("POST", "/usage-logs/archive-before", "archive_usage_logs_before"),
    ("POST", "/usage-logs/clear", "clear_usage_logs"),
    ("POST", "/usage-logs/clear-before", "clear_usage_logs_before"),
    ("GET", "/usage-archive", "usage_archive_page"),
    ("GET", "/usage-archive/export", "export_archive_excel"),
    ("POST", "/usage-archive/restore", "restore_archive_logs"),
    ("POST", "/usage-archive/restore-before", "restore_archive_logs_before"),
    ("POST", "/usage-archive/clear", "clear_archive_logs"),
]
