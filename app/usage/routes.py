from app import legacy


usage_logs_page = legacy.usage_logs_page

ROUTES = [
    ("GET", "/usage-logs", "usage_logs_page"),
]
