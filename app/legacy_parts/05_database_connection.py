# Auto-split from app/legacy.py lines 1423-1458. Loaded by app.legacy.
def init_connection_pool():
    global _connection_pool
    if is_sqlite_database_url():
        return None
    if _connection_pool is None:
        _connection_pool = pool.ThreadedConnectionPool(
            DB_POOL_MINCONN,
            DB_POOL_MAXCONN,
            get_database_url(),
            connect_timeout=10,
        )
    return _connection_pool


def get_connection():
    if is_sqlite_database_url():
        return SQLiteCompatConnection(get_sqlite_db_path())
    return init_connection_pool().getconn()


def release_connection(conn, close=False):
    if conn is None:
        return
    if is_sqlite_database_url():
        try:
            conn.close()
        except Exception:
            pass
        return
    try:
        init_connection_pool().putconn(conn, close=close)
    except Exception:
        try:
            conn.close()
        except Exception:
            pass
