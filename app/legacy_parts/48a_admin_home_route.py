# داشبورد الإدارة الرئيسي بالتصميم الجديد — يحل محل /dashboard القديم.

from flask import render_template, request, session


def _admin_home_view():
    """يعرض admin/home.html بالسايد بار الموحَّد + KPIs."""
    from app.services.radius_dashboard import (
        get_radius_kpis,
        get_radius_profiles,
    )

    # KPIs محلية من DB
    total = query_one("SELECT COUNT(*) AS c FROM beneficiaries") or {}
    kpi_total_beneficiaries = int(total.get("c") or 0)

    pending_row = query_one(
        "SELECT COUNT(*) AS c FROM radius_pending_actions WHERE status='pending'"
    ) or {}
    kpi_total_pending = int(pending_row.get("c") or 0)

    delivered_today_row = query_one(
        "SELECT COUNT(*) AS c FROM beneficiary_issued_cards WHERE DATE(issued_at)=DATE('now')"
    ) or {}
    kpi_delivered_today = int(delivered_today_row.get("c") or 0)

    # API
    api_kpis = get_radius_kpis()
    api_profiles = get_radius_profiles()

    return render_template(
        "admin/home.html",
        kpi_total_beneficiaries=kpi_total_beneficiaries,
        kpi_total_pending=kpi_total_pending,
        kpi_delivered_today=kpi_delivered_today,
        api_kpis=api_kpis,
        api_profiles=api_profiles,
    )


# ─── الـ route الجديد المنفصل ────────────────────────────────
@app.route("/admin/home", methods=["GET"])
@admin_login_required
def admin_home():
    return _admin_home_view()


# ─── Override للـ /dashboard القديم ──────────────────────────
# يحفظ النسخة القديمة (للوصول عبر /dashboard?legacy=1)
_legacy_dashboard_view = app.view_functions.get("dashboard")


@login_required
def _new_dashboard_router():
    """الـ /dashboard: يعرض النسخة الجديدة افتراضيًا، إلا إذا ?legacy=1"""
    if request.args.get("legacy") == "1" and _legacy_dashboard_view is not None:
        return _legacy_dashboard_view()
    return _admin_home_view()


# نستبدل view_function لـ dashboard
if "dashboard" in app.view_functions:
    app.view_functions["dashboard"] = _new_dashboard_router
