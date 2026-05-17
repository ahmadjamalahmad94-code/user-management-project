# Continued split from 22_beneficiary_crud_routes.py lines 99-253. Loaded by app.legacy.


@app.route("/beneficiaries/edit/<int:beneficiary_id>", methods=["GET", "POST"])
@login_required
@permission_required("edit")
def edit_beneficiary_page(beneficiary_id):
    row = query_one("SELECT * FROM beneficiaries WHERE id=%s", [beneficiary_id])
    if not row:
        flash("المستفيد غير موجود.", "error")
        return redirect(url_for("beneficiaries_page"))
    if request.method == "POST":
        data = collect_beneficiary_form()
        data["id"] = beneficiary_id
        if not is_phone_change_allowed(data.get("phone", ""), row.get("phone")):
            message = "رقم الجوال الجديد يجب أن يكون 10 أرقام بالضبط."
            if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                return jsonify({"ok": False, "message": message, "category": "error"}), 400
            flash(message, "error")
            return redirect(url_for("beneficiaries_page", user_type=row.get("user_type")))
        duplicate = find_duplicate_phone(data.get("phone"), exclude_id=beneficiary_id)
        if duplicate:
            message = f"رقم الجوال مستخدم مسبقًا للمستفيد: {safe(duplicate.get('full_name'))}."
            if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                return jsonify({"ok": False, "message": message, "category": "error"}), 400
            flash(message, "error")
            return redirect(url_for("beneficiaries_page", user_type=row.get("user_type")))
        execute_sql("""
            UPDATE beneficiaries SET
                user_type=%(user_type)s,
                first_name=%(first_name)s,
                second_name=%(second_name)s,
                third_name=%(third_name)s,
                fourth_name=%(fourth_name)s,
                full_name=%(full_name)s,
                search_name=%(search_name)s,
                phone=%(phone)s,
                tawjihi_year=%(tawjihi_year)s,
                tawjihi_branch=%(tawjihi_branch)s,
                freelancer_specialization=%(freelancer_specialization)s,
                freelancer_company=%(freelancer_company)s,
                freelancer_schedule_type=%(freelancer_schedule_type)s,
                freelancer_internet_method=%(freelancer_internet_method)s,
                freelancer_time_mode=%(freelancer_time_mode)s,
                freelancer_time_from=%(freelancer_time_from)s,
                freelancer_time_to=%(freelancer_time_to)s,
                university_name=%(university_name)s,
                university_number=%(university_number)s,
                university_college=%(university_college)s,
                university_specialization=%(university_specialization)s,
                university_days=%(university_days)s,
                university_internet_method=%(university_internet_method)s,
                university_time_mode=%(university_time_mode)s,
                university_time_from=%(university_time_from)s,
                university_time_to=%(university_time_to)s,
                notes=%(notes)s
            WHERE id=%(id)s
        """, data)
        log_action("edit", "beneficiary", beneficiary_id, f"تعديل مستفيد: {data['full_name']}")
        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            updated_row = query_one("SELECT * FROM beneficiaries WHERE id=%s", [beneficiary_id])
            current_type = clean_csv_value(request.args.get("current_user_type", ""))
            row_html, modal_html = build_beneficiary_row_html(updated_row, current_type or updated_row.get("user_type") if updated_row else current_type, build_request_args_dict(), page=1)
            return jsonify({"ok": True, "row_html": row_html, "modal_html": modal_html, "message": "تم حفظ التعديلات.", "category": "success"})
        flash("تم حفظ التعديلات.", "success")
        return redirect(url_for("beneficiaries_page", user_type=data["user_type"]))
    return render_page("تعديل مستفيد", beneficiary_form_html(row, url_for("edit_beneficiary_page", beneficiary_id=beneficiary_id), "تعديل مستفيد"))


@app.route("/beneficiaries/delete/<int:beneficiary_id>", methods=["POST"])
@login_required
@permission_required("delete")
def delete_beneficiary(beneficiary_id):
    row = query_one("SELECT full_name, user_type FROM beneficiaries WHERE id=%s", [beneficiary_id])
    if not row:
        # AJAX vs page
        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return jsonify({"ok": False, "message": "المستفيد غير موجود."}), 404
        flash("المستفيد غير موجود.", "error")
        return redirect(url_for("beneficiaries_page"))
    name = safe(row.get("full_name") or "")
    execute_sql("DELETE FROM beneficiaries WHERE id=%s", [beneficiary_id])
    log_action("delete", "beneficiary", beneficiary_id, f"حذف مستفيد: {name}")

    # ─ XHR: نرجّع JSON ونخلي الواجهة تشيل الصف بدون reload ─
    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return jsonify({"ok": True, "id": beneficiary_id, "message": "تم حذف المستفيد."})

    flash("تم حذف المستفيد.", "success")
    # نرجع لنفس الصفحة لو معرفنا الـ referrer (يحفظ الفلاتر)
    ref = request.referrer or ""
    if ref and "/admin/users-account" in ref:
        return redirect(ref)
    if ref and "/admin/cards/subscribers" in ref:
        return redirect(ref)
    redirect_type = row["user_type"] if row else ""
    return redirect(url_for("beneficiaries_page", user_type=redirect_type))



@app.route("/beneficiaries/add_usage/<int:beneficiary_id>", methods=["POST"])
@login_required
@permission_required("usage_counter")
def add_usage(beneficiary_id):
    normalize_beneficiary_usage(beneficiary_id)
    row = query_one("SELECT * FROM beneficiaries WHERE id=%s", [beneficiary_id])
    if not row:
        flash("المستفيد غير موجود.", "error")
        return redirect(url_for("beneficiaries_page"))

    usage_label, limited, count = get_usage_label(row)
    message = ""
    category = "success"

    usage_reason = clean_csv_value(request.form.get("usage_reason"))
    card_type = clean_csv_value(request.form.get("card_type"))
    usage_notes = clean_csv_value(request.form.get("usage_notes"))

    if not limited:
        message = "هذا المستفيد غير خاضع لعداد 3 مرات."
        category = "error"
    elif count >= 3:
        message = "اكتمل الحد الأسبوعي."
        category = "error"
    elif usage_reason not in USAGE_REASON_OPTIONS:
        message = "يجب اختيار سبب الحصول على البطاقة."
        category = "error"
    elif card_type not in CARD_TYPE_OPTIONS:
        message = "يجب اختيار نوع البطاقة."
        category = "error"
    else:
        execute_sql("UPDATE beneficiaries SET weekly_usage_count=COALESCE(weekly_usage_count,0)+1 WHERE id=%s", [beneficiary_id])
        current_now = now_local()
        execute_sql("""
            INSERT INTO beneficiary_usage_logs
            (beneficiary_id, usage_reason, card_type, usage_date, usage_time, notes, added_by_account_id, added_by_username)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
        """, [
            beneficiary_id,
            usage_reason,
            card_type,
            current_now.date(),
            current_now,
            usage_notes,
            session.get("account_id"),
            session.get("username", ""),
        ])
        log_action("usage_counter", "beneficiary", beneficiary_id, f"إضافة بطاقة لـ {safe(row['full_name'])} | السبب: {usage_reason} | النوع: {card_type}")
        message = "تمت إضافة البطاقة وحفظها في السجل التفصيلي."
        category = "success"

    flash(message, category)

    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        updated_row = query_one("SELECT * FROM beneficiaries WHERE id=%s", [beneficiary_id])
        args_dict = build_request_args_dict()
        row_html, modal_html = build_beneficiary_row_html(updated_row, args_dict.get("user_type", ""), args_dict, page=max(1, int(request.args.get("page", "1") or "1")))
        return jsonify({"ok": category == "success", "row_html": row_html, "modal_html": "", "message": message, "category": category})

    return redirect(request.referrer or url_for("beneficiaries_page"))


@app.route("/beneficiaries/reset-weekly-usage", methods=["POST"])
@login_required
@permission_required("reset_weekly_usage")
def reset_weekly_usage():
    reset_start = get_week_start(today_local() + timedelta(days=1))
    execute_sql("""
        UPDATE beneficiaries
        SET weekly_usage_count = 0, weekly_usage_week_start = %s
        WHERE weekly_usage_count IS DISTINCT FROM 0 OR weekly_usage_week_start IS DISTINCT FROM %s
    """, [reset_start, reset_start])
    log_action("reset_weekly_usage", "beneficiary", None, f"تصفير يدوي لكل البطاقات - week_start={reset_start}")
    flash("تم تجديد جميع البطاقات يدويًا بنجاح.", "success")
    return redirect(request.referrer or url_for("beneficiaries_page"))
