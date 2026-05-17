# 48u_fix_admin_aliases.py — يحل المشكلة الجذرية:
#
# 1) aliases من 37_admin_alias_portal_routes.py تستدعي functions القديمة مباشرة
#    (مثلاً admin_beneficiaries_alias تستدعي beneficiaries_page() بالاسم) فتتجاوز
#    الـ view_function overrides.
#
# 2) aliases من 48i_url_reorganization.py سجّلت add_url_rule(view_func=...) قبل
#    أن يحدث override في 48o/48r. لذلك view_func الذي حُفظ هو القديم.
#
# الحل: استبدال view_function لكل endpoint مشبوه بـ wrapper يبحث وقت التشغيل
# عن الـ canonical view_function (المُحدَّث بعد كل overrides).

from flask import request as _request


# ───────────────────────────────────────────────
# A) aliases من 37 (admin_*_alias) → endpoint canonical
# ───────────────────────────────────────────────
_NAMED_ALIASES = {
    "admin_beneficiaries_alias":  "beneficiaries_page",
    "admin_accounts_alias":       "accounts_page",
    "admin_profile_alias":        "profile_page",
    "admin_audit_log_alias":      "audit_log_page",
    "admin_usage_logs_alias":     "usage_logs_page",
    "admin_import_alias":         "import_page",
    "admin_exports_alias":        "export_center",
    "admin_archive_alias":        "usage_archive_page",
    "admin_cleanup_alias":        "admin_control_panel",
    "admin_timer_alias":          "power_timer_page",
}


def _make_wrapper(canonical_endpoint: str):
    """Wrapper يبحث وقت التشغيل عن view_function الـ canonical."""
    def _wrapped(**kwargs):
        target = app.view_functions.get(canonical_endpoint)
        if target is None:
            from flask import abort
            abort(404)
        return target(**kwargs)
    _wrapped.__name__ = f"_dyn__{canonical_endpoint}"
    return _wrapped


for alias_endpoint, canonical_endpoint in _NAMED_ALIASES.items():
    if alias_endpoint in app.view_functions:
        app.view_functions[alias_endpoint] = _make_wrapper(canonical_endpoint)


# ───────────────────────────────────────────────
# B) aliases من 48i (_alias__<canonical>__...) → نفس الـ canonical
# ───────────────────────────────────────────────
# 48i ينشئ endpoints بصيغة "_alias__<canonical>__..." لكل URL alias،
# والـ view_func المحفوظ مرتبط بالـ snapshot القديم. نعيد ربطه بـ dynamic lookup.

for endpoint_name in list(app.view_functions.keys()):
    if not endpoint_name.startswith("_alias__"):
        continue
    # استخراج الـ canonical من اسم الـ endpoint:
    # "_alias__<canonical>__<encoded_url>"
    rest = endpoint_name[len("_alias__"):]
    parts = rest.split("__", 1)
    if not parts:
        continue
    canonical = parts[0]
    if canonical and canonical in app.view_functions:
        app.view_functions[endpoint_name] = _make_wrapper(canonical)
