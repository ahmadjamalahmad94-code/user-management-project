# Auto-split from app/legacy.py lines 4458-4720. Loaded by app.legacy.
def beneficiary_form_html(data=None, action="", title=""):
    selected_type = clean_csv_value((data or {}).get("user_type") or request.args.get("user_type", "tawjihi")) or "tawjihi"
    links = "".join([
        f"<a class='menu-card' href='{url_for('add_beneficiary_page')}?user_type=tawjihi'><div class='menu-icon'><i class='fa-solid fa-user-graduate'></i></div><h3>توجيهي</h3><p>سنة التوجيهي والفرع.</p></a>",
        f"<a class='menu-card' href='{url_for('add_beneficiary_page')}?user_type=university'><div class='menu-icon'><i class='fa-solid fa-building-columns'></i></div><h3>جامعة</h3><p>جامعة، كلية، تخصص.</p></a>",
        f"<a class='menu-card' href='{url_for('add_beneficiary_page')}?user_type=freelancer'><div class='menu-icon'><i class='fa-solid fa-laptop-code'></i></div><h3>فري لانسر</h3><p>شركة، تخصص، إنترنت.</p></a>",
    ])
    form = format_modal_fields(
        {**(data or {}), "user_type": selected_type},
        action=action,
        scope_id="standalone-beneficiary-form",
        submit_label="حفظ",
        show_type_selector=False,
        fixed_user_type=selected_type,
    )
    return f"""
    <div class="hero"><h1>{title}</h1><p>أدخل البيانات الخاصة بالمستفيد في هذه الصفحة المخصصة.</p></div>
    <div class="card">{form}</div>
    """


def is_valid_new_phone(phone: str) -> bool:
    phone = normalize_phone(phone)
    return len(phone) == 10

def is_phone_change_allowed(phone: str, original_phone: str | None = None) -> bool:
    phone = normalize_phone(phone)
    original_phone = normalize_phone(original_phone or "")
    if not phone:
        return False
    if phone == original_phone and len(original_phone) != 10:
        return True
    return len(phone) == 10


def collect_beneficiary_form():
    data = {}
    for col in CSV_IMPORT_COLUMNS:
        val = clean_csv_value(request.form.get(col, ""))
        if col == "phone":
            val = normalize_phone(val)
        data[col] = val
    data["full_name"] = full_name_from_parts(data["first_name"], data["second_name"], data["third_name"], data["fourth_name"])
    data["search_name"] = normalize_search_ar(data["full_name"])
    data["weekly_usage_week_start"] = get_week_start()
    return data


@app.route("/beneficiaries/add", methods=["GET", "POST"])
@login_required
@permission_required("add")
def add_beneficiary_page():
    if request.method == "POST":
        data = collect_beneficiary_form()
        if not is_valid_new_phone(data.get("phone", "")):
            flash("رقم الجوال للمستفيد الجديد يجب أن يكون 10 أرقام بالضبط.", "error")
            return render_page("إضافة مستفيد", beneficiary_form_html(data, action=url_for("add_beneficiary_page"), title=page_title_map.get(data.get('user_type') or clean_csv_value(request.args.get('user_type', 'tawjihi')) or 'tawjihi', "إضافة مستفيد")))
        duplicate = find_duplicate_phone(data.get("phone"))
        if duplicate:
            flash(f"رقم الجوال مستخدم مسبقًا للمستفيد: {safe(duplicate.get('full_name'))}.", "error")
            return render_page("إضافة مستفيد", beneficiary_form_html(data, action=url_for("add_beneficiary_page"), title=page_title_map.get(data.get('user_type') or clean_csv_value(request.args.get('user_type', 'tawjihi')) or 'tawjihi', "إضافة مستفيد")))
        data["added_by_account_id"] = session.get("account_id")
        data["added_by_username"] = session.get("username")
        try:
            row = execute_sql("""
                INSERT INTO beneficiaries (
                    user_type, first_name, second_name, third_name, fourth_name, full_name, search_name, phone,
                    tawjihi_year, tawjihi_branch, freelancer_specialization, freelancer_company,
                    freelancer_schedule_type, freelancer_internet_method, freelancer_time_mode,
                    freelancer_time_from, freelancer_time_to, university_name, university_number, university_college,
                    university_specialization, university_days, university_internet_method,
                    university_time_mode, university_time_from, university_time_to,
                    weekly_usage_count, weekly_usage_week_start, notes, added_by_account_id, added_by_username
                ) VALUES (
                    %(user_type)s, %(first_name)s, %(second_name)s, %(third_name)s, %(fourth_name)s, %(full_name)s, %(search_name)s, %(phone)s,
                    %(tawjihi_year)s, %(tawjihi_branch)s, %(freelancer_specialization)s, %(freelancer_company)s,
                    %(freelancer_schedule_type)s, %(freelancer_internet_method)s, %(freelancer_time_mode)s,
                    %(freelancer_time_from)s, %(freelancer_time_to)s, %(university_name)s, %(university_number)s, %(university_college)s,
                    %(university_specialization)s, %(university_days)s, %(university_internet_method)s,
                    %(university_time_mode)s, %(university_time_from)s, %(university_time_to)s,
                    0, %(weekly_usage_week_start)s, %(notes)s, %(added_by_account_id)s, %(added_by_username)s
                ) RETURNING id
            """, data, fetchone=True)
        except psycopg2.Error:
            flash("رقم الجوال مستخدم مسبقًا للمستفيد.", "error")
            return redirect(url_for("beneficiaries_page", user_type=data["user_type"]))
        new_id = row['id'] if row else None
        log_action("add", "beneficiary", new_id, f"إضافة مستفيد: {data['full_name']}")
        flash("تمت إضافة المستفيد.", "success")
        return redirect(url_for("beneficiaries_page", user_type=data["user_type"]))
    page_user_type = clean_csv_value(request.args.get("user_type", "tawjihi")) or "tawjihi"
    page_title_map = {
        "tawjihi": "إضافة طالب توجيهي",
        "university": "إضافة طالب جامعي",
        "freelancer": "إضافة فري لانسر",
    }
    return render_page("إضافة مستفيد", beneficiary_form_html(action=url_for("add_beneficiary_page"), title=page_title_map.get(page_user_type, "إضافة مستفيد")))
