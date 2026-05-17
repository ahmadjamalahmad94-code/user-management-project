# Continued split from 22_beneficiary_crud_routes.py lines 254-264. Loaded by app.legacy.


def find_existing_beneficiary(cur, data):
    if data.get("phone"):
        cur.execute("SELECT id FROM beneficiaries WHERE phone=%s LIMIT 1", [data["phone"]])
        row = cur.fetchone()
        if row:
            return row[0]
    cur.execute("SELECT id FROM beneficiaries WHERE full_name=%s AND user_type=%s LIMIT 1", [data["full_name"], data["user_type"]])
    row = cur.fetchone()
    return row[0] if row else None
