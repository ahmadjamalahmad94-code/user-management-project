# /import + /exports بالتصميم الجديد — override يستخدم القالب الموحَّد.

from flask import render_template, request, session


def _import_v2_view():
    """صفحة استيراد CSV بالـ unified sidebar."""
    last_task_id = session.get("last_import_task_id", "")
    last_task = None
    if last_task_id:
        try:
            last_task = get_import_task(last_task_id)
        except Exception:
            last_task = None

    return render_template(
        "admin/imports/import.html",
        last_task=last_task,
    )


def _exports_v2_view():
    """مركز التصدير بالـ unified sidebar."""
    raw_unis = distinct_values("university_name", "university") or []
    universities = []
    for x in raw_unis:
        if isinstance(x, dict):
            v = x.get("value") or next(iter(x.values()), "")
        else:
            v = x
        if v:
            universities.append(str(v))

    return render_template(
        "admin/exports/exports.html",
        universities=universities,
    )


# ─── Override /import القديم ──────────────────────────
_legacy_import_view = app.view_functions.get("import_page")


@login_required
@permission_required("import")
def _new_import_router():
    if request.args.get("legacy") == "1" and _legacy_import_view is not None:
        return _legacy_import_view()
    return _import_v2_view()


if "import_page" in app.view_functions:
    app.view_functions["import_page"] = _new_import_router


# ─── Override /exports القديم ─────────────────────────
_legacy_export_view = app.view_functions.get("export_center")


@login_required
@permission_required("export")
def _new_exports_router():
    if request.args.get("legacy") == "1" and _legacy_export_view is not None:
        return _legacy_export_view()
    return _exports_v2_view()


if "export_center" in app.view_functions:
    app.view_functions["export_center"] = _new_exports_router
