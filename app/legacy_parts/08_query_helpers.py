# Auto-split from app/legacy.py lines 1810-1855. Loaded by app.legacy.
from app.db import configure_query_helpers, execute_sql, query_all, query_one, safe

configure_query_helpers(get_connection=get_connection, release_connection=release_connection)
