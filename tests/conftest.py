import os
import tempfile

os.environ.setdefault("HOBEHUB_LOCAL_DEMO", "1")
os.environ.setdefault(
    "HOBEHUB_LOCAL_DB_PATH",
    os.path.join(tempfile.gettempdir(), "hobehub_pytest.sqlite3"),
)
os.environ.setdefault("HOBEHUB_LOCAL_DEMO_SEED", "1")

from app import app as flask_app  # noqa: E402


def extract_csrf(html: str) -> str:
    for marker in ['name="_csrf_token" value="', 'name="csrf-token" content="']:
        start = html.find(marker)
        if start != -1:
            start += len(marker)
            end = html.find('"', start)
            return html[start:end] if end != -1 else ""
    return ""


def visible_text(html: str) -> str:
    import re
    from html import unescape

    html = re.sub(r"<script.*?</script>|<style.*?</style>", " ", html, flags=re.S | re.I)
    text = re.sub(r"<[^>]+>", " ", html)
    return re.sub(r"\s+", " ", unescape(text)).strip()


def login_admin(client):
    response = client.get("/login")
    token = extract_csrf(response.get_data(as_text=True))
    assert token
    return client.post(
        "/login",
        data={"username": "admin", "password": "123456", "_csrf_token": token},
        follow_redirects=True,
    )


@flask_app.template_filter("noop_for_tests")
def noop_for_tests(value):
    return value


import pytest  # noqa: E402


@pytest.fixture()
def app():
    flask_app.config.update(TESTING=True)
    return flask_app


@pytest.fixture()
def client(app):
    return app.test_client()
