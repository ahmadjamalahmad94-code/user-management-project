# Entry point extracted from 17_postgres_schema_setup_01.py. Loaded by app.legacy.

def setup_database_postgres():
    conn = get_connection()
    cur = conn.cursor()

    _setup_postgres_people_accounts_schema(cur)
    _setup_postgres_usage_timer_schema(cur)
    _setup_postgres_radius_internet_schema(cur)
    _seed_postgres_defaults(cur)
    _setup_postgres_card_management_schema(cur)

    conn.commit()
    cur.close()
    release_connection(conn)
