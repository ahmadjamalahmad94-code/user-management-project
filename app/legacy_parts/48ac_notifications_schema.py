def _ensure_notifications_schema():
    if is_sqlite_database_url():
        execute_sql(
            """
            CREATE TABLE IF NOT EXISTS notifications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                recipient_type TEXT NOT NULL CHECK (recipient_type IN ('admin','beneficiary')),
                recipient_id INTEGER NULL,
                title TEXT NOT NULL,
                body TEXT DEFAULT '',
                event_type TEXT DEFAULT '',
                status TEXT DEFAULT '',
                source_type TEXT DEFAULT '',
                source_id INTEGER NULL,
                action_url TEXT DEFAULT '',
                actor_type TEXT DEFAULT '',
                actor_id INTEGER NULL,
                actor_name TEXT DEFAULT '',
                read_at TIMESTAMP NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
    else:
        execute_sql(
            """
            CREATE TABLE IF NOT EXISTS notifications (
                id SERIAL PRIMARY KEY,
                recipient_type TEXT NOT NULL CHECK (recipient_type IN ('admin','beneficiary')),
                recipient_id INTEGER NULL,
                title TEXT NOT NULL,
                body TEXT DEFAULT '',
                event_type TEXT DEFAULT '',
                status TEXT DEFAULT '',
                source_type TEXT DEFAULT '',
                source_id INTEGER NULL,
                action_url TEXT DEFAULT '',
                actor_type TEXT DEFAULT '',
                actor_id INTEGER NULL,
                actor_name TEXT DEFAULT '',
                read_at TIMESTAMP NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
    execute_sql("CREATE INDEX IF NOT EXISTS notifications_recipient_idx ON notifications (recipient_type, recipient_id, read_at, created_at)")
    execute_sql("CREATE INDEX IF NOT EXISTS notifications_source_idx ON notifications (source_type, source_id)")


try:
    _ensure_notifications_schema()
except Exception:
    pass
