# Auto-split from app/legacy.py lines 145-243. Loaded by app.legacy.
class SQLiteCompatCursor:
    def __init__(self, conn: "SQLiteCompatConnection", cursor: sqlite3.Cursor, dict_rows: bool = False):
        self.connection = conn
        self._cursor = cursor
        self._dict_rows = dict_rows

    def execute(self, sql, params=None):
        translated_sql, translated_params = _adapt_sqlite_sql(sql, params)
        self._cursor.execute(translated_sql, translated_params)
        return self

    def executemany(self, sql, seq_of_params):
        translated_sql = _translate_sqlite_sql(sql)
        prepared = []
        for params in seq_of_params:
            _, translated_params = _adapt_sqlite_sql(sql, params)
            prepared.append(translated_params)
        self._cursor.executemany(translated_sql, prepared)
        return self

    def fetchone(self):
        row = self._cursor.fetchone()
        return _sqlite_convert_row(row, self._dict_rows)

    def fetchall(self):
        rows = self._cursor.fetchall()
        return [_sqlite_convert_row(row, self._dict_rows) for row in rows]

    def close(self):
        self._cursor.close()

    @property
    def lastrowid(self):
        return self._cursor.lastrowid


class SQLiteCompatConnection:
    def __init__(self, path: str):
        self._conn = sqlite3.connect(path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._conn.execute("PRAGMA foreign_keys = ON")

    def cursor(self, cursor_factory=None):
        return SQLiteCompatCursor(self, self._conn.cursor(), dict_rows=(cursor_factory is RealDictCursor))

    def commit(self):
        self._conn.commit()

    def rollback(self):
        self._conn.rollback()

    def close(self):
        self._conn.close()


def _sqlite_convert_row(row, dict_rows: bool):
    if row is None:
        return None
    if dict_rows:
        return {key: row[key] for key in row.keys()}
    return row


def _prepare_sqlite_param(value):
    if isinstance(value, Json):
        value = getattr(value, "adapted", value)
    if isinstance(value, (dict, list, tuple)):
        return json.dumps(value, ensure_ascii=False)
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, datetime):
        return value.isoformat(sep=" ", timespec="seconds")
    if isinstance(value, date):
        return value.isoformat()
    return value


def _translate_sqlite_sql(sql: str) -> str:
    translated = sql
    translated = translated.replace("ILIKE", "LIKE")
    translated = translated.replace("ilike", "like")
    translated = translated.replace("btrim(", "trim(")
    translated = translated.replace("BTRIM(", "TRIM(")
    translated = translated.replace("'{}'::jsonb", "'{}'")
    translated = translated.replace("::jsonb", "")
    translated = re.sub(r"\bJSONB\b", "TEXT", translated)
    translated = re.sub(r"\bIS\s+DISTINCT\s+FROM\s+(%s|\?)", r"IS NOT \1", translated, flags=re.IGNORECASE)
    translated = re.sub(r"%s", "?", translated)
    translated = re.sub(r"%\(([A-Za-z_][A-Za-z0-9_]*)\)s", r":\1", translated)
    return translated


def _adapt_sqlite_sql(sql: str, params=None):
    translated = _translate_sqlite_sql(sql)
    if params is None:
        return translated, []
    if isinstance(params, dict):
        return translated, {key: _prepare_sqlite_param(value) for key, value in params.items()}
    return translated, [_prepare_sqlite_param(value) for value in params]
