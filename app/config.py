from __future__ import annotations

import os
from zoneinfo import ZoneInfo

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover - dependency may be absent in old installs
    load_dotenv = None

if load_dotenv:
    load_dotenv()

SECRET_KEY = os.getenv("FLASK_SECRET_KEY", "")
DEFAULT_DATABASE_URL = os.getenv("DEFAULT_DATABASE_URL", "")
DB_POOL_MINCONN = int(os.getenv("DB_POOL_MINCONN", "1"))
DB_POOL_MAXCONN = int(os.getenv("DB_POOL_MAXCONN", "12"))
IMPORT_BATCH_SIZE = int(os.getenv("IMPORT_BATCH_SIZE", "250"))
MIKROTIK_HOTSPOT_URL = os.getenv("MIKROTIK_HOTSPOT_URL", "").strip().rstrip("/")
APP_TZ = ZoneInfo("Asia/Gaza")
