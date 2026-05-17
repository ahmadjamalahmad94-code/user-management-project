from __future__ import annotations

import argparse
import json
import os
import sqlite3
import sys
from pathlib import Path
from urllib.parse import urlparse

try:
    import psycopg2
except ImportError:  # pragma: no cover - user-facing CLI guard
    psycopg2 = None

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover
    load_dotenv = None


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SQLITE_PATH = ROOT / "instance" / "hobehub_local_demo.sqlite3"
IGNORED_LOCAL_TABLES = {"sqlite_sequence"}
CRITICAL_TABLES = {
    "beneficiaries",
    "beneficiary_portal_accounts",
    "beneficiary_issued_cards",
    "available_cards",
    "card_categories",
    "card_quota_policies",
    "radius_pending_actions",
    "notifications",
    "app_accounts",
}


def _load_env_files() -> None:
    if not load_dotenv:
        return
    load_dotenv(ROOT / ".env")
    load_dotenv(ROOT / ".env.render.local", override=True)


def _mask_url(database_url: str) -> str:
    parsed = urlparse(database_url)
    host = parsed.hostname or "unknown-host"
    db = parsed.path.lstrip("/") or "unknown-db"
    return f"{parsed.scheme}://***:***@{host}/{db}"


def _looks_like_placeholder(database_url: str) -> bool:
    parsed = urlparse(database_url)
    placeholders = {"user", "password", "host", "dbname", "database", "port"}
    parts = {
        (parsed.username or "").lower(),
        (parsed.password or "").lower(),
        (parsed.hostname or "").lower(),
        parsed.path.lstrip("/").lower(),
    }
    return bool(parts & placeholders)


def _sqlite_schema(path: Path) -> dict[str, dict[str, str]]:
    if not path.exists():
        raise FileNotFoundError(f"Local SQLite database not found: {path}")
    con = sqlite3.connect(str(path))
    con.row_factory = sqlite3.Row
    try:
        rows = con.execute(
            """
            SELECT name
            FROM sqlite_master
            WHERE type='table'
            ORDER BY name
            """
        ).fetchall()
        schema: dict[str, dict[str, str]] = {}
        for row in rows:
            table = row["name"]
            if table in IGNORED_LOCAL_TABLES or table.startswith("sqlite_"):
                continue
            cols = con.execute(f'PRAGMA table_info("{table}")').fetchall()
            schema[table] = {col["name"]: (col["type"] or "").upper() for col in cols}
        return schema
    finally:
        con.close()


def _postgres_schema(database_url: str) -> dict[str, dict[str, str]]:
    if psycopg2 is None:
        raise RuntimeError("psycopg2 is not installed. Run: python -m pip install -r requirements.txt")
    conn = psycopg2.connect(database_url, connect_timeout=12)
    try:
        conn.set_session(readonly=True, autocommit=False)
        with conn.cursor() as cur:
            cur.execute("SET default_transaction_read_only = on")
            cur.execute(
                """
                SELECT table_name, column_name, data_type
                FROM information_schema.columns
                WHERE table_schema = 'public'
                ORDER BY table_name, ordinal_position
                """
            )
            schema: dict[str, dict[str, str]] = {}
            for table, column, data_type in cur.fetchall():
                schema.setdefault(table, {})[column] = data_type
        conn.rollback()
        return schema
    finally:
        conn.close()


def _postgres_counts(database_url: str, tables: set[str]) -> dict[str, int | str]:
    if psycopg2 is None:
        return {}
    conn = psycopg2.connect(database_url, connect_timeout=12)
    counts: dict[str, int | str] = {}
    try:
        conn.set_session(readonly=True, autocommit=False)
        with conn.cursor() as cur:
            cur.execute("SET default_transaction_read_only = on")
            for table in sorted(tables):
                try:
                    cur.execute(f'SELECT COUNT(*) FROM "{table}"')
                    counts[table] = int(cur.fetchone()[0])
                except Exception as exc:  # keep report going
                    conn.rollback()
                    counts[table] = f"error: {type(exc).__name__}"
        conn.rollback()
    finally:
        conn.close()
    return counts


def _compare(local: dict[str, dict[str, str]], remote: dict[str, dict[str, str]]) -> dict:
    local_tables = set(local)
    remote_tables = set(remote)
    missing_tables = sorted(local_tables - remote_tables)
    extra_tables = sorted(remote_tables - local_tables)

    missing_columns: dict[str, list[str]] = {}
    extra_columns: dict[str, list[str]] = {}
    for table in sorted(local_tables & remote_tables):
        local_cols = set(local[table])
        remote_cols = set(remote[table])
        missing = sorted(local_cols - remote_cols)
        extra = sorted(remote_cols - local_cols)
        if missing:
            missing_columns[table] = missing
        if extra:
            extra_columns[table] = extra

    critical_missing = sorted((CRITICAL_TABLES & set(missing_tables)) | {t for t in missing_columns if t in CRITICAL_TABLES})
    return {
        "ok": not missing_tables and not missing_columns,
        "local_table_count": len(local_tables),
        "remote_table_count": len(remote_tables),
        "missing_tables": missing_tables,
        "missing_columns": missing_columns,
        "extra_tables": extra_tables,
        "extra_columns": extra_columns,
        "critical_missing": critical_missing,
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Read-only compatibility check between local HobeHub SQLite schema and Render PostgreSQL schema."
    )
    parser.add_argument("--database-url-env", default="DATABASE_URL", help="Environment variable containing Render DB URL.")
    parser.add_argument("--sqlite-path", default=os.getenv("HOBEHUB_LOCAL_DB_PATH") or str(DEFAULT_SQLITE_PATH))
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON.")
    args = parser.parse_args()

    explicit_database_url = (os.getenv(args.database_url_env) or "").strip()
    _load_env_files()
    database_url = explicit_database_url or (os.getenv(args.database_url_env) or "").strip()
    if not database_url:
        print(
            "No Render database URL found.\n"
            f"Create {ROOT / '.env.render.local'} with:\n"
            f"{args.database_url_env}=postgresql://USER:PASSWORD@HOST:5432/DBNAME\n"
            "Then run this script again. The script is read-only and will not modify the database.",
            file=sys.stderr,
        )
        return 2
    if not database_url.startswith(("postgresql://", "postgres://")):
        print(f"{args.database_url_env} must be a PostgreSQL URL, got: {_mask_url(database_url)}", file=sys.stderr)
        return 2
    if _looks_like_placeholder(database_url):
        print(
            "The Render database URL still contains placeholder values.\n"
            f"Current value: {_mask_url(database_url)}\n"
            "Replace USER, PASSWORD, HOST, and DBNAME with the real External Database URL from Render.",
            file=sys.stderr,
        )
        return 2
    if database_url.startswith("postgres://"):
        database_url = "postgresql://" + database_url[len("postgres://") :]
    if "sslmode=" not in database_url:
        sep = "&" if "?" in database_url else "?"
        database_url = f"{database_url}{sep}sslmode=require"

    sqlite_path = Path(args.sqlite_path)
    local = _sqlite_schema(sqlite_path)
    try:
        remote = _postgres_schema(database_url)
    except Exception as exc:
        print(
            "Could not connect to the Render database.\n"
            f"Database: {_mask_url(database_url)}\n"
            f"Reason: {type(exc).__name__}: {exc}",
            file=sys.stderr,
        )
        return 2
    report = _compare(local, remote)
    report["render_database"] = _mask_url(database_url)
    report["local_sqlite"] = str(sqlite_path)
    report["critical_counts"] = _postgres_counts(database_url, CRITICAL_TABLES & set(remote))

    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(f"Render DB: {report['render_database']}")
        print(f"Local SQLite: {report['local_sqlite']}")
        print(f"Tables: local={report['local_table_count']} render={report['remote_table_count']}")
        print(f"Result: {'PASS' if report['ok'] else 'FAIL'}")
        if report["missing_tables"]:
            print("\nMissing tables on Render:")
            for table in report["missing_tables"]:
                print(f"  - {table}")
        if report["missing_columns"]:
            print("\nMissing columns on Render:")
            for table, columns in report["missing_columns"].items():
                print(f"  - {table}: {', '.join(columns)}")
        if report["critical_missing"]:
            print("\nCritical gaps:")
            for item in report["critical_missing"]:
                print(f"  - {item}")
        if report["extra_tables"]:
            print(f"\nExtra Render tables: {len(report['extra_tables'])} (usually OK for old production data)")
        print("\nCritical table row counts:")
        for table, count in sorted(report["critical_counts"].items()):
            print(f"  - {table}: {count}")
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
