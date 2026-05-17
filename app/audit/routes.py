from app import legacy


audit_log_page = legacy.audit_log_page

ROUTES = [
    ("GET", "/audit-log", "audit_log_page"),
]
