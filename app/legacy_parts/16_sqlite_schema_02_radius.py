# Split helper extracted from 16_sqlite_schema.py. Loaded by app.legacy.

def _setup_sqlite_radius_schema(cur):
    cur.execute("""
    CREATE TABLE IF NOT EXISTS radius_api_settings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        base_url TEXT,
        master_api_key_encrypted TEXT,
        admin_username TEXT,
        service_username TEXT,
        router_login_url TEXT DEFAULT '',
        workday_start_time TEXT DEFAULT '08:00',
        workday_end_time TEXT DEFAULT '16:00',
        api_enabled INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    try:
        cur.execute("ALTER TABLE radius_api_settings ADD COLUMN router_login_url TEXT DEFAULT ''")
    except Exception:
        pass
    try:
        cur.execute("ALTER TABLE radius_api_settings ADD COLUMN admin_username TEXT")
    except Exception:
        pass
    try:
        cur.execute("ALTER TABLE radius_api_settings ADD COLUMN service_username TEXT")
    except Exception:
        pass
    try:
        cur.execute("ALTER TABLE radius_api_settings ADD COLUMN api_enabled INTEGER DEFAULT 0")
    except Exception:
        pass
    try:
        cur.execute("ALTER TABLE radius_api_settings ADD COLUMN created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
    except Exception:
        pass
    try:
        cur.execute("ALTER TABLE radius_api_settings ADD COLUMN updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
    except Exception:
        pass
    try:
        cur.execute("ALTER TABLE radius_api_settings ADD COLUMN workday_start_time TEXT DEFAULT '08:00'")
    except Exception:
        pass
    try:
        cur.execute("ALTER TABLE radius_api_settings ADD COLUMN workday_end_time TEXT DEFAULT '16:00'")
    except Exception:
        pass

    cur.execute("""
    CREATE TABLE IF NOT EXISTS radius_api_sessions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        api_key TEXT,
        expires_at TIMESTAMP NULL,
        last_login_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS beneficiary_radius_accounts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        beneficiary_id INTEGER NOT NULL REFERENCES beneficiaries(id) ON DELETE CASCADE,
        external_user_id TEXT NULL,
        external_username TEXT,
        current_profile_id TEXT NULL,
        current_profile_name TEXT NULL,
        original_profile_id TEXT NULL,
        status TEXT DEFAULT 'pending',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    cur.execute("CREATE UNIQUE INDEX IF NOT EXISTS beneficiary_radius_accounts_beneficiary_idx ON beneficiary_radius_accounts (beneficiary_id)")
