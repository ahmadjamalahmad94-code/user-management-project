# Split helper extracted from 17_postgres_schema_setup_01.py. Loaded by app.legacy.

def _seed_postgres_defaults(cur):
    cur.execute("""
        INSERT INTO radius_api_settings (base_url, admin_username, service_username, api_enabled)
        SELECT '', '', '', FALSE
        WHERE NOT EXISTS (SELECT 1 FROM radius_api_settings)
    """)

    for perm in PERMISSIONS:
        cur.execute("INSERT INTO permissions (name) VALUES (%s) ON CONFLICT (name) DO NOTHING", [perm])

    cur.execute("SELECT id FROM app_accounts WHERE username='admin' LIMIT 1")
    admin_row = cur.fetchone()
    initial_admin_password = get_initial_admin_password()
    if not admin_row:
        if initial_admin_password:
            cur.execute("""
                INSERT INTO app_accounts (username, password_hash, full_name, is_active)
                VALUES (%s,%s,%s,TRUE)
                RETURNING id
            """, [os.getenv("HOBEHUB_ADMIN_USERNAME", "admin"), admin_password_hash(initial_admin_password), "System Administrator"])
            admin_id = cur.fetchone()[0]
        else:
            admin_id = None
    else:
        admin_id = admin_row[0]

    if admin_id:
        cur.execute("""
            INSERT INTO account_permissions (account_id, permission_id)
            SELECT %s, id FROM permissions
            ON CONFLICT DO NOTHING
        """, [admin_id])
