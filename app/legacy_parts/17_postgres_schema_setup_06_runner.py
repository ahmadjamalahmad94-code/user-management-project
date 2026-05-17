# Continued split from 17_postgres_schema_setup.py lines 388-399. Loaded by app.legacy.


def setup_database():
    if is_sqlite_database_url():
        return setup_database_sqlite()
    return setup_database_postgres()


try:
    setup_database()
except psycopg2.Error:
    logging.getLogger("hobehub.database").exception("Database initialization failed")
