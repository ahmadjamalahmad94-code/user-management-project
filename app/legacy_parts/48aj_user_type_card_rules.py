# 48aj_user_type_card_rules.py
# قواعد فئات البطاقات المسموحة حسب نوع المشترك — قابلة للتعديل من الإدارة
# يستبدل القاعدة المُبرمجة في access_rules.py بقاعدة قابلة للتحرير عبر:
#   GET  /admin/cards/user-type-rules         → صفحة الإدارة
#   POST /admin/cards/user-type-rules/save    → حفظ التعديلات
#
# جدول user_type_card_rules:
#   user_type           TEXT PRIMARY KEY   (tawjihi / university / freelancer)
#   allowed_codes_csv   TEXT               (مثلاً "half_hour" أو "half_hour,one_hour" أو "" = كل الفئات)
#   skip_reason         INTEGER (0/1)      (يتخطى مودال "سبب البطاقة" عند المشترك)
#   whatsapp_group_url  TEXT               رابط مجموعة واتساب الخاصة بالفئة
#   updated_at          TIMESTAMP

from flask import jsonify

# ────────────────────────────────────────────────────────────────
# Bootstrap الجدول + البذرة الافتراضية
# ────────────────────────────────────────────────────────────────
def _ensure_user_type_card_rules_schema():
    try:
        if is_sqlite_database_url():
            execute_sql(
                """
                CREATE TABLE IF NOT EXISTS user_type_card_rules (
                    user_type         TEXT PRIMARY KEY,
                    allowed_codes_csv TEXT NOT NULL DEFAULT '',
                    skip_reason       INTEGER NOT NULL DEFAULT 0,
                    whatsapp_group_url TEXT NOT NULL DEFAULT '',
                    updated_at        TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
        else:
            execute_sql(
                """
                CREATE TABLE IF NOT EXISTS user_type_card_rules (
                    user_type         TEXT PRIMARY KEY,
                    allowed_codes_csv TEXT NOT NULL DEFAULT '',
                    skip_reason       SMALLINT NOT NULL DEFAULT 0,
                    whatsapp_group_url TEXT NOT NULL DEFAULT '',
                    updated_at        TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
    except Exception:
        pass
    try:
        execute_sql("ALTER TABLE user_type_card_rules ADD COLUMN whatsapp_group_url TEXT NOT NULL DEFAULT ''")
    except Exception:
        pass

    # بذرة افتراضية: التوجيهي → نصف ساعة فقط + يتخطى السبب
    try:
        seed = [
            ("tawjihi",    "half_hour", 1),
            ("university", "",          0),
            ("freelancer", "",          0),
        ]
        for ut, codes, skip in seed:
            existing = query_one(
                "SELECT user_type FROM user_type_card_rules WHERE user_type=%s",
                [ut],
            )
            if not existing:
                execute_sql(
                    """
                    INSERT INTO user_type_card_rules (user_type, allowed_codes_csv, skip_reason)
                    VALUES (%s, %s, %s)
                    """,
                    [ut, codes, skip],
                )
    except Exception:
        pass


_ensure_user_type_card_rules_schema()


# ────────────────────────────────────────────────────────────────
# واجهات الاستعلام (تُستخدم من access_rules وغيره)
# ────────────────────────────────────────────────────────────────
def get_user_type_rule(user_type):
    """يعيد {'allowed_codes_csv': str, 'skip_reason': int} أو None لو ما في قاعدة."""
    if not user_type:
        return None
    ut = (user_type or "").strip().lower()
    return query_one(
        "SELECT user_type, allowed_codes_csv, skip_reason, whatsapp_group_url FROM user_type_card_rules WHERE user_type=%s",
        [ut],
    )


def get_user_type_allowed_codes(user_type):
    """يعيد tuple بالأكواد المسموحة لنوع المشترك، أو None لو كل الفئات مسموحة."""
    rule = get_user_type_rule(user_type)
    if not rule:
        return None
    csv_val = (rule.get("allowed_codes_csv") or "").strip()
    if not csv_val:
        return None  # فارغ = الكل مسموح
    return tuple(c.strip().lower() for c in csv_val.split(",") if c.strip())


def should_skip_reason_for_user_type(user_type):
    """هل يتخطى مودال السبب لهذا النوع؟"""
    rule = get_user_type_rule(user_type)
    if not rule:
        return False
    return bool(int(rule.get("skip_reason") or 0))


def normalize_whatsapp_group_url(raw_url):
    url = clean_csv_value(raw_url or "")
    if not url:
        return ""
    if url.startswith("chat.whatsapp.com/") or url.startswith("wa.me/"):
        url = "https://" + url
    if not (url.startswith("https://") or url.startswith("http://")):
        return ""
    return url


def whatsapp_group_url_for_user_type(user_type):
    rule = get_user_type_rule(user_type)
    if not rule:
        return ""
    return normalize_whatsapp_group_url(rule.get("whatsapp_group_url"))


# ────────────────────────────────────────────────────────────────
# صفحة الإدارة
# ────────────────────────────────────────────────────────────────
_USER_TYPE_DISPLAY = [
    ("tawjihi",    "توجيهي",   "fa-user-graduate"),
    ("university", "جامعي",    "fa-school"),
    ("freelancer", "عمل حر",   "fa-briefcase"),
]

_ALL_CARD_CODES = [
    ("half_hour",   "نصف ساعة",  30),
    ("one_hour",    "ساعة",      60),
    ("two_hours",   "ساعتين",    120),
    ("three_hours", "3 ساعات",   180),
    ("four_hours",  "4 ساعات",   240),
]


@app.route("/admin/cards/user-type-rules", methods=["GET"])
@admin_login_required
def admin_user_type_card_rules_page():
    rows = query_all("SELECT * FROM user_type_card_rules ORDER BY user_type ASC") or []
    rules_by_type = {r["user_type"]: r for r in rows}

    rules_view = []
    for ut, label, icon in _USER_TYPE_DISPLAY:
        r = rules_by_type.get(ut) or {"allowed_codes_csv": "", "skip_reason": 0}
        allowed = [c.strip().lower() for c in (r.get("allowed_codes_csv") or "").split(",") if c.strip()]
        rules_view.append({
            "user_type": ut,
            "label": label,
            "icon": icon,
            "allowed_codes": allowed,
            "skip_reason": bool(int(r.get("skip_reason") or 0)),
            "whatsapp_group_url": r.get("whatsapp_group_url") or "",
        })

    return render_template(
        "admin/cards/user_type_rules.html",
        rules=rules_view,
        all_codes=_ALL_CARD_CODES,
    )


@app.route("/admin/cards/user-type-rules/save", methods=["POST"])
@admin_login_required
def admin_user_type_card_rules_save():
    try:
        for ut, _label, _icon in _USER_TYPE_DISPLAY:
            # القيم تأتي كقائمة checkboxes اسمها codes_<ut>
            codes = request.form.getlist(f"codes_{ut}")
            codes_csv = ",".join(c.strip().lower() for c in codes if c.strip())
            skip = 1 if request.form.get(f"skip_reason_{ut}") else 0
            whatsapp_group_url = normalize_whatsapp_group_url(request.form.get(f"whatsapp_group_url_{ut}"))
            execute_sql(
                """
                INSERT INTO user_type_card_rules (user_type, allowed_codes_csv, skip_reason, whatsapp_group_url, updated_at)
                VALUES (%s, %s, %s, %s, CURRENT_TIMESTAMP)
                ON CONFLICT(user_type) DO UPDATE SET
                    allowed_codes_csv = excluded.allowed_codes_csv,
                    skip_reason = excluded.skip_reason,
                    whatsapp_group_url = excluded.whatsapp_group_url,
                    updated_at = CURRENT_TIMESTAMP
                """
                if is_sqlite_database_url() else
                """
                INSERT INTO user_type_card_rules (user_type, allowed_codes_csv, skip_reason, whatsapp_group_url, updated_at)
                VALUES (%s, %s, %s, %s, CURRENT_TIMESTAMP)
                ON CONFLICT (user_type) DO UPDATE SET
                    allowed_codes_csv = EXCLUDED.allowed_codes_csv,
                    skip_reason = EXCLUDED.skip_reason,
                    whatsapp_group_url = EXCLUDED.whatsapp_group_url,
                    updated_at = CURRENT_TIMESTAMP
                """,
                [ut, codes_csv, skip, whatsapp_group_url],
            )
        log_action("user_type_card_rules_save", "user_type_card_rules", None, "تحديث قواعد البطاقات حسب النوع")
        flash("تم حفظ القواعد بنجاح.", "success")
    except Exception as e:
        flash(f"تعذّر الحفظ: {e}", "error")
    return redirect(url_for("admin_user_type_card_rules_page"))


# Helper for JSON (يستخدمه frontend لو احتجناه لاحقًا)
@app.route("/api/admin/user-type-rules", methods=["GET"])
@admin_login_required
def admin_user_type_rules_json():
    rows = query_all("SELECT * FROM user_type_card_rules ORDER BY user_type ASC") or []
    return jsonify({"ok": True, "rules": rows})
