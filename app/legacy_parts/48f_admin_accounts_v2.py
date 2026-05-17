# /accounts بالتصميم الجديد — override يستخدم القالب الجديد.

from flask import render_template, request


def _accounts_v2_view():
    """قائمة المستخدمين والصلاحيات بالـ unified sidebar."""
    rows = query_all(
        """
        SELECT a.*,
               COALESCE(string_agg(p.name, ',' ORDER BY p.name), '') AS perms
        FROM app_accounts a
        LEFT JOIN account_permissions ap ON ap.account_id = a.id
        LEFT JOIN permissions p ON p.id = ap.permission_id
        GROUP BY a.id
        ORDER BY a.id DESC
        """
    )

    accounts = []
    active_count = 0
    for r in rows:
        rec = dict(r)
        perms_str = rec.get("perms") or ""
        rec["permission_list"] = [x.strip() for x in str(perms_str).split(",") if x.strip()]
        if rec.get("is_active"):
            active_count += 1
        accounts.append(rec)

    inactive_count = len(accounts) - active_count

    return render_template(
        "admin/accounts/list.html",
        accounts=accounts,
        active_count=active_count,
        inactive_count=inactive_count,
        permission_label=permission_label,
    )


# ─── Override /accounts القديم ──────────────────────────
_legacy_accounts_view = app.view_functions.get("accounts_page")


@login_required
@permission_required("manage_accounts")
def _new_accounts_router():
    """الـ /accounts: التصميم الجديد افتراضيًا، القديم عبر ?legacy=1"""
    if request.args.get("legacy") == "1" and _legacy_accounts_view is not None:
        return _legacy_accounts_view()
    return _accounts_v2_view()


if "accounts_page" in app.view_functions:
    app.view_functions["accounts_page"] = _new_accounts_router
