# 48aq_master_admin_portal.py
# ─────────────────────────────────────────────────────────────────────
# بوابة دخول الإدارة الفاخرة على رابط سرّي:
#
#     /h0be-vault-9k2x7p/master-gateway
#
# لا يوجد أي ربط لها من صفحة الإقلاع أو أي navigation — تُكتشف فقط بمعرفة الرابط.
# تستخدم نفس backend الـ AJAX الموجود في 48ai_unified_login.py:
#     POST /login/check  → التحقق من وجود الحساب
#     POST /login/submit → التحقق من كلمة المرور
#
# لو أردت تغيير المسار: عدّل المتغير _MASTER_PORTAL_PATH أدناه.

from flask import render_template, redirect, session, url_for


# ─── المسار السري ───────────────────────────────────────────────────
_MASTER_PORTAL_PATH = "/h0be-vault-9k2x7p/master-gateway"


def _master_admin_portal_view():
    """يعرض القالب الفاخر لدخول الإدارة.

    لو في session فعّال (مدير مسجّل): يحوّل مباشرة لداشبورد الإدارة.
    """
    if session.get("account_id"):
        try:
            return redirect(url_for("dashboard"))
        except Exception:
            return redirect("/admin/dashboard")
    return render_template("auth/master_admin_portal.html")


# سجّل الرابط في Flask مع endpoint مستقل (للحفاظ على البوابة القديمة كاحتياط)
try:
    app.add_url_rule(
        _MASTER_PORTAL_PATH,
        endpoint="master_admin_portal",
        view_func=_master_admin_portal_view,
        methods=["GET"],
    )
except AssertionError:
    # endpoint موجود سابقاً (إعادة تحميل في dev) — تجاهل
    pass
