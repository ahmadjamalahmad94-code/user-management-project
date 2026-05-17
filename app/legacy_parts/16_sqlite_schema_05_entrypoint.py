# Entry point extracted from 16_sqlite_schema.py. Loaded by app.legacy.

def setup_database_sqlite():
    conn = get_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    _setup_sqlite_people_usage_schema(cur)
    _setup_sqlite_radius_schema(cur)
    _setup_sqlite_portal_card_schema(cur)
    _seed_sqlite_defaults(cur)
    _setup_sqlite_card_management_schema(cur)

    conn.commit()
    cur.close()
    release_connection(conn)
