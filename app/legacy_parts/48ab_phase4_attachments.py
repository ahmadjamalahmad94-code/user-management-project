# 48ab_phase4_attachments.py
# Phase 4 — المرفقات والمراسلات (للصفحة الشخصية)
# - جدول user_attachments + user_messages
# - رفع/حذف/تنزيل مرفقات
# - إضافة/قائمة ملاحظات وشكاوي

import logging
import os
import uuid
from pathlib import Path as _Path  # alias لأن legacy.py يحذف Path من globals بعد التحميل
from flask import request, jsonify, send_from_directory, abort, session

_log = logging.getLogger("hobehub.phase4_attachments")


# ────────────────────────────────────────────────────────────────
# Schema (idempotent) — مع نوع id مناسب لكل DB
# على SQLite: SERIAL لا يعمل auto-increment → نستخدم INTEGER PRIMARY KEY
# على Postgres: نحتاج SERIAL أو IDENTITY
# ────────────────────────────────────────────────────────────────
try:
    _IS_SQLITE = is_sqlite_database_url()
except Exception:
    _IS_SQLITE = True

_ID_TYPE = "INTEGER PRIMARY KEY AUTOINCREMENT" if _IS_SQLITE else "SERIAL PRIMARY KEY"

# Recovery: لو الجدول القديم اتعمل بـ SERIAL على SQLite، الـ ids كلها NULL.
# نسقطه ونعيد إنشاءه (البيانات الموجودة مكسورة فعلاً ولا يمكن استرجاعها بالـ id).
for _tbl in ("user_attachments", "user_messages"):
    try:
        broken = query_one("SELECT 1 AS x FROM " + _tbl + " WHERE id IS NULL LIMIT 1")
        if broken:
            _log.warning("table %s has NULL ids (broken schema) — dropping and recreating", _tbl)
            execute_sql("DROP TABLE " + _tbl)
    except Exception:
        pass  # الجدول غير موجود بعد، سنُنشئه فيما يلي

for _stmt in (
    f"""CREATE TABLE IF NOT EXISTS user_attachments (
        id {_ID_TYPE},
        beneficiary_id INTEGER NOT NULL,
        kind TEXT,
        label TEXT,
        file_name TEXT NOT NULL,
        stored_name TEXT NOT NULL,
        file_size BIGINT DEFAULT 0,
        uploaded_by TEXT,
        uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )""",
    f"""CREATE TABLE IF NOT EXISTS user_messages (
        id {_ID_TYPE},
        beneficiary_id INTEGER NOT NULL,
        kind TEXT DEFAULT 'note',
        body TEXT,
        by_username TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )""",
    "CREATE INDEX IF NOT EXISTS user_attachments_bid_idx ON user_attachments(beneficiary_id)",
    "CREATE INDEX IF NOT EXISTS user_messages_bid_idx ON user_messages(beneficiary_id)",
):
    try:
        execute_sql(_stmt)
    except Exception as e:
        msg = str(e).lower()
        if "already exists" in msg or "duplicate" in msg:
            _log.debug("phase4 schema skipped (already applied): %s", _stmt.split('(')[0].strip())
        else:
            _log.warning(
                "phase4 schema bootstrap FAILED for %s | error: %s",
                _stmt.split('(')[0].strip(), e,
            )


# ────────────────────────────────────────────────────────────────
# Storage folder — يُسجَّل بوضوح لو فشل إنشاؤه (يعني الرفع لاحقاً 500 cryptic)
# ────────────────────────────────────────────────────────────────
_ATTACH_DIR = _Path(__file__).resolve().parents[1] / "uploads" / "user_attachments"
try:
    _ATTACH_DIR.mkdir(parents=True, exist_ok=True)
    if not os.access(str(_ATTACH_DIR), os.W_OK):
        _log.warning(
            "attachments dir created but NOT WRITABLE: %s — uploads will fail at runtime",
            _ATTACH_DIR,
        )
except Exception as e:
    _log.error(
        "FAILED to create attachments directory %s: %s — uploads will fail",
        _ATTACH_DIR, e,
    )

ALLOWED_EXT = {".pdf", ".jpg", ".jpeg", ".png", ".webp", ".doc", ".docx", ".xls", ".xlsx", ".txt", ".zip"}
MAX_MB = 8


def _ext_ok(filename):
    return _Path(filename).suffix.lower() in ALLOWED_EXT


# ────────────────────────────────────────────────────────────────
# GET /admin/users/<id>/attachments — قائمة المرفقات
# ────────────────────────────────────────────────────────────────
@app.route("/admin/users/<int:beneficiary_id>/attachments")
@login_required
def admin_user_attachments_list(beneficiary_id):
    rows = query_all(
        """
        SELECT id, kind, label, file_name, stored_name, file_size, uploaded_by, uploaded_at
        FROM user_attachments WHERE beneficiary_id=%s ORDER BY id DESC
        """,
        [beneficiary_id],
    ) or []
    return jsonify({"ok": True, "items": [
        {
            "id": r["id"], "kind": r.get("kind") or "other",
            "label": r.get("label") or r.get("file_name"),
            "file_name": r.get("file_name"), "size": int(r.get("file_size") or 0),
            "uploaded_by": r.get("uploaded_by") or "",
            "uploaded_at": str(r.get("uploaded_at") or ""),
            "url": f"/admin/users/{beneficiary_id}/attachments/{r['id']}/download",
        } for r in rows
    ]})


# ────────────────────────────────────────────────────────────────
# POST /admin/users/<id>/attachments — رفع مرفق
# ────────────────────────────────────────────────────────────────
@app.route("/admin/users/<int:beneficiary_id>/attachments", methods=["POST"])
@login_required
@permission_required("edit")
def admin_user_attachments_upload(beneficiary_id):
    if "file" not in request.files:
        return jsonify({"ok": False, "message": "لم يتم اختيار ملف."}), 400
    file = request.files["file"]
    if not file or not file.filename:
        return jsonify({"ok": False, "message": "اسم الملف فارغ."}), 400
    if not _ext_ok(file.filename):
        return jsonify({"ok": False, "message": "نوع الملف غير مسموح."}), 400

    # Size check
    file.seek(0, 2)
    size = file.tell()
    file.seek(0)
    if size > MAX_MB * 1024 * 1024:
        return jsonify({"ok": False, "message": f"حجم الملف يتجاوز {MAX_MB} ميجابايت."}), 400

    kind = clean_csv_value(request.form.get("kind") or "other")
    label = clean_csv_value(request.form.get("label") or file.filename)

    # Save with unique name
    ext = _Path(file.filename).suffix.lower()
    stored_name = f"{beneficiary_id}_{uuid.uuid4().hex}{ext}"
    stored_path = _ATTACH_DIR / stored_name
    file.save(str(stored_path))

    row = execute_sql(
        """
        INSERT INTO user_attachments
            (beneficiary_id, kind, label, file_name, stored_name, file_size, uploaded_by)
        VALUES (%s,%s,%s,%s,%s,%s,%s)
        RETURNING id
        """,
        [beneficiary_id, kind, label, file.filename, stored_name, size, session.get("username") or ""],
        fetchone=True,
    )
    new_id = row["id"] if row and row.get("id") else None
    if not new_id:
        saved = query_one(
            "SELECT id FROM user_attachments WHERE beneficiary_id=%s AND stored_name=%s ORDER BY id DESC LIMIT 1",
            [beneficiary_id, stored_name],
        )
        new_id = (saved or {}).get("id")
    if not new_id and _IS_SQLITE:
        saved = query_one(
            "SELECT rowid AS rid, id FROM user_attachments WHERE beneficiary_id=%s AND stored_name=%s ORDER BY rowid DESC LIMIT 1",
            [beneficiary_id, stored_name],
        )
        if saved and saved.get("rid"):
            new_id = int(saved["rid"])
            execute_sql("UPDATE user_attachments SET id=%s WHERE rowid=%s", [new_id, new_id])
    log_action("attachment_upload", "beneficiary", beneficiary_id, f"رفع: {file.filename}")
    try:
        from app.services.notification_service import notify_beneficiary_attachment_uploaded
        notify_beneficiary_attachment_uploaded(
            beneficiary_id,
            file.filename,
            session.get("username") or "",
            attachment_id=int(new_id or 0) or None,
            uploaded_by_kind="admin",
        )
    except Exception:
        pass
    return jsonify({"ok": True, "message": "تم رفع الملف.", "id": new_id})


# ────────────────────────────────────────────────────────────────
# GET /admin/users/<id>/attachments/<aid>/download
# ────────────────────────────────────────────────────────────────
@app.route("/admin/users/<int:beneficiary_id>/attachments/<int:aid>/download")
@login_required
def admin_user_attachment_download(beneficiary_id, aid):
    row = query_one(
        "SELECT stored_name, file_name FROM user_attachments WHERE id=%s AND beneficiary_id=%s",
        [aid, beneficiary_id],
    )
    if not row:
        abort(404)
    # ?inline=1 → عرض داخل المتصفح (للـ lightbox)، بدونه → تنزيل
    inline = request.args.get("inline") == "1"
    return send_from_directory(
        str(_ATTACH_DIR), row["stored_name"],
        as_attachment=not inline,
        download_name=row.get("file_name") or row["stored_name"],
    )


# ────────────────────────────────────────────────────────────────
# POST /admin/users/<id>/attachments/<aid>/delete
# ────────────────────────────────────────────────────────────────
@app.route("/admin/users/<int:beneficiary_id>/attachments/<int:aid>/delete", methods=["POST"])
@login_required
@permission_required("delete")
def admin_user_attachment_delete(beneficiary_id, aid):
    row = query_one(
        "SELECT stored_name, file_name FROM user_attachments WHERE id=%s AND beneficiary_id=%s",
        [aid, beneficiary_id],
    )
    if not row:
        return jsonify({"ok": False, "message": "المرفق غير موجود."}), 404
    try:
        (_ATTACH_DIR / row["stored_name"]).unlink(missing_ok=True)
    except Exception as e:
        _log.warning(
            "failed to remove physical file %s during delete (DB row removed anyway): %s",
            row.get("stored_name"), e,
        )
    execute_sql("DELETE FROM user_attachments WHERE id=%s", [aid])
    log_action("attachment_delete", "beneficiary", beneficiary_id, f"حذف: {row.get('file_name')}")
    return jsonify({"ok": True, "message": "تم حذف المرفق."})


# ────────────────────────────────────────────────────────────────
# GET /admin/users/<id>/messages — قائمة الملاحظات/الشكاوي
# ────────────────────────────────────────────────────────────────
@app.route("/admin/users/<int:beneficiary_id>/messages")
@login_required
def admin_user_messages_list(beneficiary_id):
    rows = query_all(
        "SELECT id, kind, body, by_username, created_at FROM user_messages WHERE beneficiary_id=%s ORDER BY id DESC",
        [beneficiary_id],
    ) or []
    return jsonify({"ok": True, "items": [
        {"id": r["id"], "kind": r.get("kind") or "note", "body": r.get("body") or "",
         "by_username": r.get("by_username") or "", "created_at": str(r.get("created_at") or "")}
        for r in rows
    ]})


# ────────────────────────────────────────────────────────────────
# POST /admin/users/<id>/messages — إضافة ملاحظة
# ────────────────────────────────────────────────────────────────
@app.route("/admin/users/<int:beneficiary_id>/messages", methods=["POST"])
@login_required
def admin_user_messages_add(beneficiary_id):
    kind = clean_csv_value(request.form.get("kind") or "note")
    body = clean_csv_value(request.form.get("body") or "")
    if not body:
        return jsonify({"ok": False, "message": "النص فارغ."}), 400
    row = execute_sql(
        "INSERT INTO user_messages (beneficiary_id, kind, body, by_username) VALUES (%s,%s,%s,%s) RETURNING id",
        [beneficiary_id, kind, body, session.get("username") or ""],
        fetchone=True,
    )
    message_id = row["id"] if row and row.get("id") else None
    if not message_id and _IS_SQLITE:
        saved = query_one(
            """
            SELECT rowid AS rid, id
            FROM user_messages
            WHERE beneficiary_id=%s AND body=%s
            ORDER BY rowid DESC LIMIT 1
            """,
            [beneficiary_id, body],
        )
        if saved and saved.get("rid"):
            message_id = int(saved["rid"])
            execute_sql("UPDATE user_messages SET id=%s WHERE rowid=%s", [message_id, message_id])
    log_action("user_message_add", "beneficiary", beneficiary_id, f"ملاحظة: {body[:80]}")
    try:
        from app.services.notification_service import notify_beneficiary_message_added
        notify_beneficiary_message_added(
            beneficiary_id,
            kind,
            body,
            session.get("username") or "",
            message_id=int(message_id or 0) or None,
        )
    except Exception:
        pass
    return jsonify({"ok": True, "message": "تم الحفظ.", "id": message_id})


# ────────────────────────────────────────────────────────────────
# POST /admin/users/<id>/messages/<mid>/delete
# ────────────────────────────────────────────────────────────────
@app.route("/admin/users/<int:beneficiary_id>/messages/<int:mid>/delete", methods=["POST"])
@login_required
@permission_required("delete")
def admin_user_message_delete(beneficiary_id, mid):
    row = query_one("SELECT id FROM user_messages WHERE id=%s AND beneficiary_id=%s", [mid, beneficiary_id])
    if not row:
        return jsonify({"ok": False, "message": "غير موجود."}), 404
    execute_sql("DELETE FROM user_messages WHERE id=%s", [mid])
    log_action("user_message_delete", "beneficiary", beneficiary_id, f"حذف ملاحظة #{mid}")
    return jsonify({"ok": True, "message": "تم الحذف."})


def portal_messages_for(beneficiary_id, limit=20):
    rows = query_all(
        """
        SELECT id, kind, body, by_username, created_at
        FROM user_messages
        WHERE beneficiary_id=%s
        ORDER BY id DESC
        LIMIT %s
        """,
        [beneficiary_id, int(limit or 20)],
    ) or []
    labels = {
        "note": "ملاحظة",
        "warning": "تحذير",
        "complaint": "شكوى",
        "reminder": "تذكير",
        "info": "تنبيه",
    }
    icons = {
        "note": "fa-message",
        "warning": "fa-triangle-exclamation",
        "complaint": "fa-circle-exclamation",
        "reminder": "fa-bell",
        "info": "fa-circle-info",
    }
    result = []
    for row in rows:
        item = dict(row)
        kind = (item.get("kind") or "note").strip().lower()
        item["kind_label"] = labels.get(kind, "رسالة")
        item["kind_icon"] = icons.get(kind, "fa-message")
        result.append(item)
    return result


@app.context_processor
def _inject_portal_messages_helper():
    return {"portal_messages_for": portal_messages_for}
