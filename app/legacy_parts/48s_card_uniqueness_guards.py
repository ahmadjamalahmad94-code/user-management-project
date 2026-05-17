def _dedupe_card_tables_before_unique_indexes():
    if is_sqlite_database_url():
        execute_sql(
            """
            DELETE FROM manual_access_cards
            WHERE id NOT IN (
                SELECT MIN(id)
                FROM manual_access_cards
                GROUP BY LOWER(TRIM(card_username))
            )
            """
        )
        execute_sql(
            """
            DELETE FROM manual_access_cards
            WHERE LOWER(TRIM(card_username)) IN (
                SELECT LOWER(TRIM(card_username))
                FROM beneficiary_issued_cards
            )
            """
        )
        execute_sql(
            """
            DELETE FROM beneficiary_issued_cards
            WHERE id NOT IN (
                SELECT MIN(id)
                FROM beneficiary_issued_cards
                GROUP BY LOWER(TRIM(card_username))
            )
            """
        )
    else:
        execute_sql(
            """
            DELETE FROM manual_access_cards mac
            USING manual_access_cards keep
            WHERE LOWER(BTRIM(mac.card_username)) = LOWER(BTRIM(keep.card_username))
              AND mac.id > keep.id
            """
        )
        execute_sql(
            """
            DELETE FROM manual_access_cards mac
            USING beneficiary_issued_cards bic
            WHERE LOWER(BTRIM(mac.card_username)) = LOWER(BTRIM(bic.card_username))
            """
        )
        execute_sql(
            """
            DELETE FROM beneficiary_issued_cards bic
            USING beneficiary_issued_cards keep
            WHERE LOWER(BTRIM(bic.card_username)) = LOWER(BTRIM(keep.card_username))
              AND bic.id > keep.id
            """
        )


def _ensure_card_uniqueness_indexes():
    if is_sqlite_database_url():
        execute_sql(
            """
            CREATE UNIQUE INDEX IF NOT EXISTS manual_access_cards_unique_username_idx
            ON manual_access_cards (LOWER(TRIM(card_username)))
            """
        )
        execute_sql(
            """
            CREATE UNIQUE INDEX IF NOT EXISTS beneficiary_issued_cards_unique_username_idx
            ON beneficiary_issued_cards (LOWER(TRIM(card_username)))
            """
        )
    else:
        execute_sql(
            """
            CREATE UNIQUE INDEX IF NOT EXISTS manual_access_cards_unique_username_idx
            ON manual_access_cards (LOWER(BTRIM(card_username)))
            """
        )
        execute_sql(
            """
            CREATE UNIQUE INDEX IF NOT EXISTS beneficiary_issued_cards_unique_username_idx
            ON beneficiary_issued_cards (LOWER(BTRIM(card_username)))
            """
        )


try:
    _dedupe_card_tables_before_unique_indexes()
    _ensure_card_uniqueness_indexes()
except Exception:
    pass
