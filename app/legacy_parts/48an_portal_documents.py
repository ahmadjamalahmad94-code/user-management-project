# 48an_portal_documents.py
# رفع مستندات من بوابة المشترك حسب user_type
#
# المسارات:
#   POST /user/profile/upload-document  → رفع ملف
#   GET  /user/profile/documents        → قائمة مستنداتي
#   POST /user/profile/documents/<id>/delete → حذف مستند (خاص بصاحبه)

from flask import request, redirect, url_for, flash, send_from_directory, abort, jsonify, session
from pathlib import Path as _Path
from werkzeug.utils import secure_filename
import os
import uuid


_DOCS_DIR = _Path(__file__).resolve().parents[1] / "uploads" / "user_attachments"
_DOCS_DIR.mkdir(parents=True, exist_ok=True)

_ALLOWED_EXT = {".pdf", ".png", ".jpg", ".jpeg", ".webp", ".doc", ".docx"}
_MAX_FILE_MB = 8


def _portal_docs_is_sqlite():
    try:
        return is_sqlite_database_url()
    except Exception:
        return True


def _portal_docs_column_names():
    try:
        if _portal_docs_is_sqlite():
            return {row.get("name") for row in (query_all("PRAGMA table_info(user_attachments)") or [])}
        rows = query_all(
            """
            SELECT column_name AS name
            FROM information_schema.columns
            WHERE table_name=%s
            """,
            ["user_attachments"],
        )
        return {row.get("name") for row in (rows or [])}
    except Exception:
        return set()


def _portal_docs_add_column_if_missing(column_name, definition):
    if column_name in _portal_docs_column_names():
        return
    try:
        if _portal_docs_is_sqlite():
            execute_sql(f"ALTER TABLE user_attachments ADD COLUMN {definition}")
        else:
            execute_sql(f"ALTER TABLE user_attachments ADD COLUMN IF NOT EXISTS {definition}")
    except Exception as exc:
        if "duplicate column" not in str(exc).lower() and "already exists" not in str(exc).lower():
            raise


def _ensure_portal_documents_schema():
    id_type = "INTEGER PRIMARY KEY AUTOINCREMENT" if _portal_docs_is_sqlite() else "SERIAL PRIMARY KEY"
    try:
        execute_sql(
            f"""
            CREATE TABLE IF NOT EXISTS user_attachments (
                id {id_type},
                beneficiary_id INTEGER NOT NULL,
                kind TEXT DEFAULT '',
                label TEXT DEFAULT '',
                file_name TEXT NOT NULL,
                stored_name TEXT NOT NULL,
                file_size BIGINT DEFAULT 0,
                file_size_bytes BIGINT DEFAULT 0,
                mime_type TEXT DEFAULT '',
                note TEXT DEFAULT '',
                uploaded_by TEXT DEFAULT '',
                uploaded_by_kind TEXT DEFAULT '',
                uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        for column_name, definition in [
            ("kind", "kind TEXT DEFAULT ''"),
            ("label", "label TEXT DEFAULT ''"),
            ("file_size", "file_size BIGINT DEFAULT 0"),
            ("file_size_bytes", "file_size_bytes BIGINT DEFAULT 0"),
            ("mime_type", "mime_type TEXT DEFAULT ''"),
            ("note", "note TEXT DEFAULT ''"),
            ("uploaded_by", "uploaded_by TEXT DEFAULT ''"),
            ("uploaded_by_kind", "uploaded_by_kind TEXT DEFAULT ''"),
            ("uploaded_at", "uploaded_at TIMESTAMP NULL"),
        ]:
            _portal_docs_add_column_if_missing(column_name, definition)

        execute_sql(
            """
            UPDATE user_attachments
            SET file_size_bytes=COALESCE(NULLIF(file_size_bytes, 0), file_size, 0)
            WHERE file_size IS NOT NULL
              AND (file_size_bytes IS NULL OR file_size_bytes=0)
            """
        )
        execute_sql("CREATE INDEX IF NOT EXISTS user_attachments_bid_idx ON user_attachments(beneficiary_id)")
    except Exception as exc:
        try:
            app.logger.warning("portal documents schema migration failed: %s", exc)
        except Exception:
            pass


_ensure_portal_documents_schema()


# ────────────────────────────────────────────────────────────────
# POST /user/profile/upload-document
# ────────────────────────────────────────────────────────────────
@app.route("/user/profile/upload-document", methods=["POST"])
@user_login_required
def portal_upload_document():
    bid = int(session.get("beneficiary_id") or 0)
    if not bid:
        flash("يجب تسجيل الدخول.", "error")
        return redirect(url_for("login"))

    file = request.files.get("document")
    note = (request.form.get("note") or "").strip()
    doc_type = (request.form.get("doc_type") or "general").strip()
    if not file or not file.filename:
        flash("الرجاء اختيار ملف.", "error")
        return redirect(url_for("user_profile_page"))

    fname = secure_filename(file.filename) or "document"
    ext = os.path.splitext(fname)[1].lower()
    if ext not in _ALLOWED_EXT:
        flash(f"نوع الملف غير مسموح. المسموح: {', '.join(_ALLOWED_EXT)}", "error")
        return redirect(url_for("user_profile_page"))

    # حدّ الحجم
    file.seek(0, os.SEEK_END)
    size_bytes = int(file.tell() or 0)
    size_mb = size_bytes / (1024 * 1024)
    file.seek(0)
    if size_mb > _MAX_FILE_MB:
        flash(f"حجم الملف كبير ({size_mb:.1f}MB). الحد الأقصى {_MAX_FILE_MB}MB.", "error")
        return redirect(url_for("user_profile_page"))

    stored_name = f"{bid}_{uuid.uuid4().hex}{ext}"
    file_path = _DOCS_DIR / stored_name
    try:
        file.save(str(file_path))
    except Exception as e:
        flash(f"تعذّر حفظ الملف: {e}", "error")
        return redirect(url_for("user_profile_page"))

    try:
        execute_sql(
            """
            INSERT INTO user_attachments
                (beneficiary_id, kind, label, file_name, stored_name, file_size, file_size_bytes,
                 mime_type, note, uploaded_by, uploaded_by_kind)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            """,
            [bid, doc_type, fname, fname, stored_name, size_bytes, size_bytes,
             file.mimetype or "", f"[{doc_type}] {note}".strip(),
             session.get("beneficiary_full_name") or "subscriber", "subscriber"],
        )
        log_action("portal_document_upload", "beneficiary", bid, f"رفع ملف: {fname} ({doc_type})")
        try:
            attachment = query_one(
                "SELECT id FROM user_attachments WHERE beneficiary_id=%s AND stored_name=%s ORDER BY id DESC LIMIT 1",
                [bid, stored_name],
            )
            attachment_id = (attachment or {}).get("id")
            if not attachment_id and _portal_docs_is_sqlite():
                attachment = query_one(
                    "SELECT rowid AS rid, id FROM user_attachments WHERE beneficiary_id=%s AND stored_name=%s ORDER BY rowid DESC LIMIT 1",
                    [bid, stored_name],
                )
                if attachment and attachment.get("rid"):
                    attachment_id = int(attachment["rid"])
                    execute_sql("UPDATE user_attachments SET id=%s WHERE rowid=%s", [attachment_id, attachment_id])
            from app.services.notification_service import notify_beneficiary_attachment_uploaded
            notify_beneficiary_attachment_uploaded(
                bid,
                fname,
                session.get("beneficiary_full_name") or "مشترك",
                attachment_id=int(attachment_id or 0) or None,
                uploaded_by_kind="beneficiary",
            )
        except Exception:
            pass
        flash(f"تم رفع الملف ({fname}) بنجاح. تساعد هذه الملفات في توثيق حسابك.", "success")
    except Exception as e:
        try:
            file_path.unlink(missing_ok=True)
        except Exception:
            pass
        flash(f"تعذّر تسجيل الملف: {e}", "error")

    return redirect(url_for("user_profile_page"))


# ────────────────────────────────────────────────────────────────
# GET /user/profile/documents/<id>/download
# ────────────────────────────────────────────────────────────────
@app.route("/user/profile/documents/<int:doc_id>/download")
@user_login_required
def portal_document_download(doc_id):
    bid = int(session.get("beneficiary_id") or 0)
    row = query_one(
        "SELECT stored_name, file_name FROM user_attachments WHERE id=%s AND beneficiary_id=%s",
        [doc_id, bid],
    )
    if not row:
        abort(404)
    return send_from_directory(
        str(_DOCS_DIR), row["stored_name"],
        as_attachment=False, download_name=row["file_name"],
    )


# ────────────────────────────────────────────────────────────────
# POST /user/profile/documents/<id>/delete
# ────────────────────────────────────────────────────────────────
@app.route("/user/profile/documents/<int:doc_id>/delete", methods=["POST"])
@user_login_required
def portal_document_delete(doc_id):
    bid = int(session.get("beneficiary_id") or 0)
    row = query_one(
        "SELECT stored_name FROM user_attachments WHERE id=%s AND beneficiary_id=%s",
        [doc_id, bid],
    )
    if not row:
        flash("الملف غير موجود.", "error")
        return redirect(url_for("user_profile_page"))
    try:
        (_DOCS_DIR / row["stored_name"]).unlink(missing_ok=True)
    except Exception:
        pass
    execute_sql("DELETE FROM user_attachments WHERE id=%s AND beneficiary_id=%s", [doc_id, bid])
    log_action("portal_document_delete", "beneficiary", bid, f"حذف ملف #{doc_id}")
    flash("تم حذف الملف.", "success")
    return redirect(url_for("user_profile_page"))


# ────────────────────────────────────────────────────────────────
# helper للقالب: قائمة مستندات مشترك
# ────────────────────────────────────────────────────────────────
def portal_documents_for(beneficiary_id):
    return query_all(
        """
        SELECT
            id,
            file_name,
            COALESCE(file_size_bytes, file_size, 0) AS file_size_bytes,
            COALESCE(mime_type, '') AS mime_type,
            COALESCE(NULLIF(note, ''), NULLIF(label, ''), NULLIF(kind, ''), '') AS note,
            uploaded_at
        FROM user_attachments WHERE beneficiary_id=%s ORDER BY id DESC
        """,
        [beneficiary_id],
    ) or []


@app.context_processor
def _inject_portal_documents_helper():
    return {"portal_documents_for": portal_documents_for}
