from __future__ import annotations

from collections.abc import Callable
from typing import Any

import psycopg2
import sqlite3
from markupsafe import escape
from psycopg2.extras import RealDictCursor


_get_connection: Callable[[], Any] | None = None
_release_connection: Callable[..., None] | None = None


def configure_query_helpers(get_connection: Callable[[], Any], release_connection: Callable[..., None]) -> None:
    global _get_connection, _release_connection
    _get_connection = get_connection
    _release_connection = release_connection


def _connection_hooks() -> tuple[Callable[[], Any], Callable[..., None]]:
    if _get_connection is None or _release_connection is None:
        raise RuntimeError("Database query helpers were used before connection hooks were configured.")
    return _get_connection, _release_connection


def query_all(sql, params=None):
    get_connection, release_connection = _connection_hooks()
    conn = get_connection()
    cur = None
    try:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute(sql, params or [])
        return cur.fetchall()
    finally:
        if cur is not None:
            cur.close()
        release_connection(conn)


def query_one(sql, params=None):
    get_connection, release_connection = _connection_hooks()
    conn = get_connection()
    cur = None
    try:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute(sql, params or [])
        return cur.fetchone()
    finally:
        if cur is not None:
            cur.close()
        release_connection(conn)


def execute_sql(sql, params=None, fetchone=False):
    get_connection, release_connection = _connection_hooks()
    conn = get_connection()
    cur = None
    try:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute(sql, params or [])
        row = cur.fetchone() if fetchone else None
        conn.commit()
        return row
    except (psycopg2.Error, sqlite3.Error):
        conn.rollback()
        raise
    finally:
        if cur is not None:
            cur.close()
        release_connection(conn)


def safe(v):
    return "" if v is None else escape(str(v))
