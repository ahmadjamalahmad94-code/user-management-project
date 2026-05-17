# 48i_url_reorganization.py
# توحيد المسارات تحت 3 namespaces واضحة:
#   /admin/*  → كل صفحات الإدارة
#   /card/*   → مشتركو البطاقات
#   /user/*   → مشتركو اليوزر (username/password)
#
# الفلسفة: لا نكسر شيئًا. نضيف الـ URLs الجديدة كـ aliases تستدعي
# نفس view_functions القديمة. الـ URLs القديمة تبقى تعمل أيضًا.
# السايد بار/الكود الجديد يستخدم الجديدة فقط.

# (endpoint, new_url, methods)
# الـ endpoint = اسم الـ Flask view function، الـ new_url = المسار الجديد
_URL_ALIASES = [
    # ───── Admin pages ─────────────────────────────────────
    ("dashboard",                    "/admin/dashboard",                                ["GET"]),
    ("accounts_page",                "/admin/accounts",                                 ["GET"]),
    ("add_account",                  "/admin/accounts/add",                             ["GET", "POST"]),
    ("edit_account",                 "/admin/accounts/edit/<int:account_id>",           ["GET", "POST"]),
    ("toggle_account",               "/admin/accounts/toggle/<int:account_id>",         ["POST"]),
    ("audit_log_page",               "/admin/audit-log",                                ["GET"]),
    ("beneficiaries_page",           "/admin/beneficiaries",                            ["GET"]),
    ("add_beneficiary_page",         "/admin/beneficiaries/add",                        ["GET", "POST"]),
    ("edit_beneficiary_page",        "/admin/beneficiaries/edit/<int:beneficiary_id>",  ["GET", "POST"]),
    ("delete_beneficiary",           "/admin/beneficiaries/delete/<int:beneficiary_id>", ["POST"]),
    ("add_usage",                    "/admin/beneficiaries/add_usage/<int:beneficiary_id>", ["POST"]),
    ("reset_weekly_usage",           "/admin/beneficiaries/reset-weekly-usage",         ["POST"]),
    ("bulk_delete_beneficiaries",    "/admin/beneficiaries/bulk-delete",                ["POST"]),
    ("export_selected_beneficiaries", "/admin/beneficiaries/export-selected",           ["POST"]),
    ("import_page",                  "/admin/import",                                   ["GET"]),
    ("import_csv",                   "/admin/import/upload",                            ["POST"]),
    ("import_status_page",           "/admin/import/<task_id>/status",                  ["GET"]),
    ("import_progress",              "/admin/import/<task_id>/progress",                ["GET"]),
    ("export_center",                "/admin/exports",                                  ["GET"]),
    ("export_csv",                   "/admin/exports/csv",                              ["GET"]),
    ("download_template",            "/admin/exports/template",                         ["GET"]),
    ("backup_sql",                   "/admin/backup-sql",                               ["GET"]),
    ("usage_logs_page",              "/admin/usage-logs",                               ["GET"]),
    ("archive_usage_logs",           "/admin/usage-logs/archive",                       ["POST"]),
    ("archive_usage_logs_before",    "/admin/usage-logs/archive-before",                ["POST"]),
    ("clear_usage_logs",             "/admin/usage-logs/clear",                         ["POST"]),
    ("clear_usage_logs_before",      "/admin/usage-logs/clear-before",                  ["POST"]),
    ("usage_archive_page",           "/admin/usage-archive",                            ["GET"]),
    ("export_archive_excel",         "/admin/usage-archive/export",                     ["GET"]),
    ("restore_archive_logs",         "/admin/usage-archive/restore",                    ["POST"]),
    ("restore_archive_logs_before",  "/admin/usage-archive/restore-before",             ["POST"]),
    ("clear_archive_logs",           "/admin/usage-archive/clear",                      ["POST"]),
    ("admin_control",                "/admin/control",                                  ["GET", "POST"]),

    # ───── Cards subscribers ──────
    ("user_cards_dashboard",         "/card",                                           ["GET"]),
    ("user_cards_request",           "/card/request",                                   ["POST"]),
    ("user_cards_history",           "/card/history",                                   ["GET"]),
    ("user_cards_pending_list",      "/card/pending",                                   ["GET"]),

    # Legacy plural card URLs kept as redirects by 48n_cleanup_legacy.py.
    ("user_cards_dashboard",         "/cards",                                          ["GET"]),
    ("user_cards_request",           "/cards/request",                                  ["POST"]),
    ("user_cards_history",           "/cards/history",                                  ["GET"]),
    ("user_cards_pending_list",      "/cards/pending",                                  ["GET"]),

    # ───── Username subscribers ─
    # The canonical routes already exist as /user/account/* and /user/internet/*.
    # Legacy plural /users/* URLs are kept as redirects by 48n_cleanup_legacy.py.
    ("user_account_dashboard",       "/users/account",                                  ["GET"]),
    ("user_account_change_password", "/users/change-password",                          ["GET", "POST"]),
    ("user_account_unblock_site",    "/users/unblock-site",                             ["GET", "POST"]),
    ("user_account_speed_upgrade",   "/users/speed-upgrade",                            ["GET", "POST"]),
    ("user_account_my_requests",     "/users/requests",                                 ["GET"]),
    ("user_internet_request_page",   "/users/internet/request",                         ["GET", "POST"]),
    ("user_internet_my_requests_page", "/users/internet/my-requests",                   ["GET"]),
    ("user_internet_my_access_page", "/users/internet/my-access",                       ["GET"]),
]


def _register_aliases():
    skipped = []
    added = []
    for endpoint, new_url, methods in _URL_ALIASES:
        view_func = app.view_functions.get(endpoint)
        if view_func is None:
            skipped.append((endpoint, new_url, "endpoint not registered"))
            continue
        alias_endpoint = (
            f"_alias__{endpoint}__"
            + new_url.strip("/").replace("/", "_").replace("<", "").replace(">", "").replace(":", "_")
        )
        if alias_endpoint in app.view_functions:
            continue
        try:
            app.add_url_rule(
                new_url,
                endpoint=alias_endpoint,
                view_func=view_func,
                methods=methods,
            )
            added.append((endpoint, new_url))
        except Exception as exc:
            skipped.append((endpoint, new_url, str(exc)))
    # احفظ تقريرًا قابلًا للقراءة من خارج
    app.config["_URL_ALIAS_REPORT"] = {"added": added, "skipped": skipped}


_register_aliases()
