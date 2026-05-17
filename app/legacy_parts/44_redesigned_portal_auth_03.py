# Continued split from 44_redesigned_portal_auth.py lines 174-292. Loaded by app.legacy.


def _redesigned_user_register():
    if request.method == "POST":
        phone = normalize_phone(request.form.get("phone"))
        track = clean_csv_value(request.form.get("user_type") or request.form.get("track"))
        first_name = clean_csv_value(request.form.get("first_name"))
        second_name = clean_csv_value(request.form.get("second_name"))
        third_name = clean_csv_value(request.form.get("third_name"))
        fourth_name = clean_csv_value(request.form.get("fourth_name"))
        if len(phone) != 10:
            flash("رقم الجوال يجب أن يكون 10 أرقام.", "error")
            return redirect(url_for("user_register"))
        if not track:
            flash("يرجى اختيار المجال.", "error")
            return redirect(url_for("user_register"))
        if not all([first_name, second_name, third_name, fourth_name]):
            flash("يرجى إدخال الاسم الرباعي كاملًا.", "error")
            return redirect(url_for("user_register"))
        signup_id = create_beneficiary_signup_request(request.form)
        log_action("beneficiary_signup_request", "beneficiary_signup_request", signup_id or 0, f"Signup request from {phone}")
        flash("تم استلام طلب الاشتراك وحفظه بانتظار مراجعة الإدارة وتحديد نوع الخدمة المناسب.", "success")
        return redirect(url_for("user_register"))
    return render_template("auth/user_register.html")


app.view_functions["portal_entry"] = _redesigned_portal_entry
app.view_functions["login"] = _redesigned_admin_login
app.view_functions["user_login"] = _redesigned_user_login
app.view_functions["user_register"] = _redesigned_user_register
