from __future__ import annotations

from flask import jsonify, redirect, render_template, url_for

from app import legacy
from app.dashboard import services as dashboard_services


def dashboard_live_api():
    legacy.normalize_all_usage()
    today = legacy.today_local()
    month_start = legacy.get_month_start(today)
    week_start = legacy.get_week_start(today)
    return jsonify(dashboard_services.dashboard_live_payload(today, month_start, week_start))


def dashboard():
    legacy.normalize_all_usage()
    today = legacy.today_local()
    week_start = legacy.get_week_start(today)
    month_start = legacy.get_month_start(today)
    dashboard_data = dashboard_services.dashboard_page_data(today, month_start, week_start)
    content = render_template(
        "dashboard/dashboard.html",
        action_type_label=legacy.action_type_label,
        format_dt_compact=legacy.format_dt_compact,
        target_type_label=legacy.target_type_label,
        **dashboard_data,
    )
    return legacy.render_page("لوحة التحكم", content)


def admin_root():
    return redirect(url_for("admin_dashboard_alias"))


def admin_dashboard_alias():
    return dashboard()


def register_dashboard_routes(flask_app):
    if "dashboard_live_api" not in flask_app.view_functions:
        flask_app.add_url_rule(
            "/api/dashboard/live",
            endpoint="dashboard_live_api",
            view_func=legacy.login_required(dashboard_live_api),
        )
    if "dashboard" not in flask_app.view_functions:
        flask_app.add_url_rule(
            "/dashboard",
            endpoint="dashboard",
            view_func=legacy.login_required(dashboard),
        )
    if "admin_root" not in flask_app.view_functions:
        flask_app.add_url_rule(
            "/admin",
            endpoint="admin_root",
            view_func=legacy.admin_login_required(admin_root),
        )
    if "admin_dashboard_alias" not in flask_app.view_functions:
        flask_app.add_url_rule(
            "/admin/dashboard",
            endpoint="admin_dashboard_alias",
            view_func=legacy.admin_login_required(admin_dashboard_alias),
        )

    legacy.dashboard_live_api = flask_app.view_functions["dashboard_live_api"]
    legacy.dashboard = flask_app.view_functions["dashboard"]
    legacy.admin_root = flask_app.view_functions["admin_root"]
    legacy.admin_dashboard_alias = flask_app.view_functions["admin_dashboard_alias"]
    return flask_app
