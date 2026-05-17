# Split helper extracted from 16_sqlite_schema.py. Loaded by app.legacy.

def _seed_sqlite_defaults(cur):
    cur.execute("INSERT OR IGNORE INTO radius_api_settings (id, base_url, admin_username, service_username, api_enabled) VALUES (1, '', '', '', 0)")

    for perm in PERMISSIONS:
        cur.execute("INSERT OR IGNORE INTO permissions (name) VALUES (%s)", [perm])

    cur.execute("SELECT id FROM app_accounts WHERE username='admin' LIMIT 1")
    admin_row = cur.fetchone()
    initial_admin_password = get_initial_admin_password()
    if not admin_row:
        if initial_admin_password:
            cur.execute(
                "INSERT INTO app_accounts (username, password_hash, full_name, is_active) VALUES (%s,%s,%s,1)",
                [os.getenv("HOBEHUB_ADMIN_USERNAME", "admin"), admin_password_hash(initial_admin_password), "System Administrator"],
            )
            admin_id = cur.lastrowid
        else:
            admin_id = None
    else:
        admin_id = admin_row["id"]

    if initial_admin_password:
        cur.execute("UPDATE app_accounts SET password_hash=%s WHERE username='admin' AND (password_hash IS NULL OR trim(password_hash)='')", [admin_password_hash(initial_admin_password)])
    if admin_id:
        cur.execute(
            """
            INSERT OR IGNORE INTO account_permissions (account_id, permission_id)
            SELECT %s, id FROM permissions
            """,
            [admin_id],
        )

    if os.getenv("HOBEHUB_LOCAL_DEMO_SEED", "0").strip().lower() in {"1", "true", "yes", "on"}:
        _seed_local_demo_data(cur)
