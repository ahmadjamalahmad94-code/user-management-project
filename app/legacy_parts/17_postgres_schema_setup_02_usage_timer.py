# Split helper extracted from 17_postgres_schema_setup_01.py. Loaded by app.legacy.

def _setup_postgres_usage_timer_schema(cur):
    cur.execute("""
    CREATE TABLE IF NOT EXISTS permissions (
        id SERIAL PRIMARY KEY,
        name TEXT UNIQUE NOT NULL
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS account_permissions (
        account_id INTEGER REFERENCES app_accounts(id) ON DELETE CASCADE,
        permission_id INTEGER REFERENCES permissions(id) ON DELETE CASCADE,
        PRIMARY KEY (account_id, permission_id)
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS audit_logs (
        id SERIAL PRIMARY KEY,
        account_id INTEGER,
        username_snapshot TEXT,
        action_type TEXT,
        target_type TEXT,
        target_id INTEGER,
        details TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS beneficiary_usage_logs (
        id SERIAL PRIMARY KEY,
        beneficiary_id INTEGER NOT NULL REFERENCES beneficiaries(id) ON DELETE CASCADE,
        usage_reason TEXT NOT NULL DEFAULT '',
        card_type TEXT NOT NULL DEFAULT 'ساعة',
        usage_date DATE NOT NULL DEFAULT CURRENT_DATE,
        usage_time TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
        notes TEXT DEFAULT '',
        added_by_account_id INTEGER,
        added_by_username TEXT DEFAULT ''
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS beneficiary_usage_logs_archive (
        archive_id SERIAL PRIMARY KEY,
        original_log_id INTEGER,
        beneficiary_id INTEGER,
        usage_reason TEXT NOT NULL DEFAULT '',
        card_type TEXT NOT NULL DEFAULT 'ساعة',
        usage_date DATE NOT NULL DEFAULT CURRENT_DATE,
        usage_time TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
        notes TEXT DEFAULT '',
        added_by_account_id INTEGER,
        added_by_username TEXT DEFAULT '',
        archived_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
        archived_by_account_id INTEGER,
        archived_by_username TEXT DEFAULT ''
    )
    """)
    cur.execute("ALTER TABLE beneficiary_usage_logs_archive ADD COLUMN IF NOT EXISTS archive_id SERIAL")
    cur.execute("ALTER TABLE beneficiary_usage_logs_archive ADD COLUMN IF NOT EXISTS original_log_id INTEGER")
    cur.execute("ALTER TABLE beneficiary_usage_logs_archive ADD COLUMN IF NOT EXISTS beneficiary_id INTEGER")
    cur.execute("ALTER TABLE beneficiary_usage_logs_archive ADD COLUMN IF NOT EXISTS usage_reason TEXT NOT NULL DEFAULT ''")
    cur.execute("ALTER TABLE beneficiary_usage_logs_archive ADD COLUMN IF NOT EXISTS card_type TEXT NOT NULL DEFAULT 'ساعة'")
    cur.execute("ALTER TABLE beneficiary_usage_logs_archive ADD COLUMN IF NOT EXISTS usage_date DATE NOT NULL DEFAULT CURRENT_DATE")
    cur.execute("ALTER TABLE beneficiary_usage_logs_archive ADD COLUMN IF NOT EXISTS usage_time TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP")
    cur.execute("ALTER TABLE beneficiary_usage_logs_archive ADD COLUMN IF NOT EXISTS notes TEXT DEFAULT ''")
    cur.execute("ALTER TABLE beneficiary_usage_logs_archive ADD COLUMN IF NOT EXISTS added_by_account_id INTEGER")
    cur.execute("ALTER TABLE beneficiary_usage_logs_archive ADD COLUMN IF NOT EXISTS added_by_username TEXT DEFAULT ''")
    cur.execute("ALTER TABLE beneficiary_usage_logs_archive ADD COLUMN IF NOT EXISTS archived_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP")
    cur.execute("ALTER TABLE beneficiary_usage_logs_archive ADD COLUMN IF NOT EXISTS archived_by_account_id INTEGER")
    cur.execute("ALTER TABLE beneficiary_usage_logs_archive ADD COLUMN IF NOT EXISTS archived_by_username TEXT DEFAULT ''")


    cur.execute("""
    CREATE TABLE IF NOT EXISTS power_timer (
        id INTEGER PRIMARY KEY,
        duration_minutes INTEGER NOT NULL DEFAULT 30,
        cycle_started_at TIMESTAMP NULL,
        paused_remaining_seconds INTEGER NULL,
        auto_restart_delay_seconds INTEGER NOT NULL DEFAULT 10,
        state TEXT NOT NULL DEFAULT 'stopped',
        updated_by_username TEXT DEFAULT '',
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    cur.execute("""
        INSERT INTO power_timer (id, duration_minutes, auto_restart_delay_seconds, state, updated_by_username)
        VALUES (1, 30, 10, 'stopped', '')
        ON CONFLICT (id) DO NOTHING
    """)
