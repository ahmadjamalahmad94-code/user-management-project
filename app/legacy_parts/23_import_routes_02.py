# Continued split from 23_import_routes.py lines 160-198. Loaded by app.legacy.


@app.route("/download_template")
@login_required
@permission_required("import")
def download_template():
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=CSV_IMPORT_COLUMNS)
    writer.writeheader()
    resp = Response(output.getvalue(), mimetype="text/csv")
    resp.headers["Content-Disposition"] = "attachment; filename=users_import_template.csv"
    return resp


@app.route("/import_csv", methods=["POST"])
@login_required
@permission_required("import")
def import_csv():
    file = request.files.get("csv_file")
    if not file or not file.filename:
        flash("اختر ملف CSV أولًا.", "error")
        return redirect(url_for("import_page"))
    try:
        content = file.read().decode("utf-8-sig")
    except UnicodeDecodeError:
        flash("الملف ليس بترميز UTF-8.", "error")
        return redirect(url_for("import_page"))

    reader = csv.DictReader(io.StringIO(content))
    if not reader.fieldnames:
        flash("الملف فارغ أو غير صالح.", "error")
        return redirect(url_for("import_page"))

    task_id = create_import_task(session.get("username", ""), session.get("account_id"), file.filename)
    session["last_import_task_id"] = task_id
    append_import_log(task_id, f"تم استلام الملف: {file.filename}")
    launch_import_task(task_id, content)
    flash("تم بدء الاستيراد في الخلفية. يمكنك متابعة التقدم المباشر الآن.", "success")
    return redirect(url_for("import_status_page", task_id=task_id))
