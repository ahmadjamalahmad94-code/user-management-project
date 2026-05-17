# Hobe Hub

Hobe Hub is a Flask application for managing beneficiaries, internet-service requests, hotspot cards, usage logs, archives, admin accounts, and RADIUS integrations.

## Local Setup

1. Create a virtual environment with Python `3.14.4`.
2. Install dependencies:

   ```powershell
   python -m pip install -r requirements.txt
   ```

3. Copy `.env.example` to `.env` and keep local demo mode enabled:

   ```powershell
   Copy-Item .env.example .env
   ```

4. Run the app:

   ```powershell
   $env:HOBEHUB_LOCAL_DEMO="1"
   python app.py
   ```

The local demo uses SQLite by default at `instance/hobehub_local_demo.sqlite3`. Demo seed data is inserted only when `HOBEHUB_LOCAL_DEMO_SEED=1`.

## Production Notes

- Set `FLASK_SECRET_KEY` to a long random value.
- Set `DATABASE_URL`; do not rely on any hard-coded database connection.
- Set `HOBEHUB_ADMIN_PASSWORD` only for first-time admin creation, then rotate/remove it.
- Keep `.env`, logs, SQLite files, and temporary HTML files out of Git.
- Use HTTPS and a process manager such as Gunicorn in production.

## Project Structure

- `app/legacy.py` is now a small compatibility loader.
- `app/legacy_parts/` contains the split legacy domains in execution order.
- `app/legacy_templates/` contains large HTML template strings that were moved out of Python code.
- New code should prefer focused modules, blueprints, services, and templates instead of adding more logic to one large file.
- Keep the numbered legacy part order stable unless a route or endpoint override explicitly needs to move.

## Verification

Run syntax and smoke checks before shipping:

```powershell
python -m ruff check app app.py wsgi.py tests
python -m compileall app app.py wsgi.py
python -m pytest -q
```

Or run the bundled verification script:

```powershell
.\scripts\verify.ps1
```

The production entrypoint is `wsgi:app`, and `/healthz` returns application and database health for deployment monitors.
