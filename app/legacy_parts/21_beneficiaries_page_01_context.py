# Beneficiaries page context extracted from 21_beneficiaries_page.py. Loaded by app.legacy.

def _beneficiaries_page_context():
    normalize_all_usage()

    args_dict = build_request_args_dict()

    try:
        page = max(1, int(request.args.get("page", "1") or "1"))
    except ValueError:
        page = 1

    per_page = 25

    filters, params = build_beneficiary_filters(args_dict)
    where = " AND ".join(filters)

    allowed_sort = {
        "id": "id",
        "full_name": "full_name",
        "phone": "phone",
        "tawjihi_year": "tawjihi_year",
        "tawjihi_branch": "tawjihi_branch",
        "university_number": "university_number",
        "university_name": "university_name",
        "university_specialization": "university_specialization",
        "freelancer_specialization": "freelancer_specialization",
        "freelancer_company": "freelancer_company",
        "weekly_usage_count": "weekly_usage_count",
        "created_at": "created_at",
    }
    sort_by = allowed_sort.get(args_dict["sort_by"], "id")
    sort_order = "ASC" if args_dict["sort_order"] == "asc" else "DESC"

    total = query_one(f"SELECT COUNT(*) AS c FROM beneficiaries WHERE {where}", params)["c"]
    pages = max(1, math.ceil(total / per_page))
    page = min(page, pages)
    offset = (page - 1) * per_page

    rows = query_all(
        f"""
        SELECT * FROM beneficiaries
        WHERE {where}
        ORDER BY {sort_by} {sort_order}, id DESC
        LIMIT %s OFFSET %s
        """,
        params + [per_page, offset],
    )

    tawjihi_years = distinct_values("tawjihi_year", "tawjihi")
    tawjihi_branches = distinct_values("tawjihi_branch", "tawjihi")
    university_names = distinct_values("university_name", "university")
    universities_colleges = distinct_values("university_college", "university")
    freelancer_companies = distinct_values("freelancer_company", "freelancer")
    freelancer_specs = distinct_values("freelancer_specialization", "freelancer")

    selected_type = args_dict["user_type"]
    tabs = [
        ("", "الكل", total if not selected_type else query_one("SELECT COUNT(*) AS c FROM beneficiaries", [])["c"]),
        ("tawjihi", "توجيهي", query_one("SELECT COUNT(*) AS c FROM beneficiaries WHERE user_type='tawjihi'")["c"]),
        ("university", "جامعة", query_one("SELECT COUNT(*) AS c FROM beneficiaries WHERE user_type='university'")["c"]),
        ("freelancer", "فري لانسر", query_one("SELECT COUNT(*) AS c FROM beneficiaries WHERE user_type='freelancer'")["c"]),
    ]
    tabs_html = ""
    for tab_value, label, count in tabs:
        tab_query = build_query_string({**args_dict, "user_type": tab_value, "page": 1})
        cls = "tab-pill active" if selected_type == tab_value else "tab-pill"
        tabs_html += f"<a class='{cls}' href='?{tab_query}'>{label} <span class='badge'>{count}</span></a>"

    metrics = {
        "النتائج الحالية": total,
        "المعروض في الصفحة": len(rows),
        "الخاضعون للحد الأسبوعي": sum(1 for r in rows if get_usage_label(r)[1]),
        "مكتملو الحد": sum(1 for r in rows if get_usage_label(r)[1] and get_usage_label(r)[2] >= 3),
    }
    metric_html = "".join([f"<div class='metric-box'><h4>{k}</h4><div class='num'>{v}</div></div>" for k, v in metrics.items()])

    if selected_type == "tawjihi":
        headers = [
            (None, "#"),
            ("full_name", "الاسم الكامل"),
            ("phone", "الجوال"),
            ("tawjihi_year", "السنة"),
            ("tawjihi_branch", "الفرع"),
            ("weekly_usage_count", "الاستخدام"),
            (None, "أضيف بواسطة"),
            ("created_at", "التاريخ"),
            (None, "ملاحظات"),
            (None, "إجراءات"),
        ]
    elif selected_type == "university":
        headers = [
            (None, "#"),
            ("full_name", "الاسم الكامل"),
            ("phone", "الجوال"),
            ("university_number", "الرقم الجامعي"),
            ("university_name", "الجامعة"),
            ("university_college", "الكلية"),
            ("university_specialization", "التخصص"),
            ("weekly_usage_count", "الاستخدام"),
            (None, "أضيف بواسطة"),
            ("created_at", "التاريخ"),
            (None, "ملاحظات"),
            (None, "إجراءات"),
        ]
    elif selected_type == "freelancer":
        headers = [
            (None, "#"),
            ("full_name", "الاسم الكامل"),
            ("phone", "الجوال"),
            ("freelancer_specialization", "التخصص"),
            ("freelancer_company", "الشركة"),
            ("weekly_usage_count", "الاستخدام"),
            (None, "أضيف بواسطة"),
            ("created_at", "التاريخ"),
            (None, "ملاحظات"),
            (None, "إجراءات"),
        ]
    else:
        headers = [
            (None, "#"),
            ("full_name", "الاسم الكامل"),
            ("phone", "الجوال"),
            (None, "النوع"),
            ("weekly_usage_count", "الاستخدام"),
            (None, "أضيف بواسطة"),
            ("created_at", "التاريخ"),
            (None, "ملاحظات"),
            (None, "إجراءات"),
        ]

    thead = "<tr>"
    for col, label in headers:
        if col:
            thead += f"<th><a href='{beneficiary_sort_link(args_dict, col)}'>{label}</a></th>"
        else:
            thead += f"<th>{label}</th>"
    can_bulk_select = has_permission('delete') or has_permission('export')
    if can_bulk_select:
        thead += "<th class='checkbox-cell'><input id='select-all' class='select-all' type='checkbox' onchange='toggleSelectAll(this)'></th>"
    thead += "</tr>"

    rows_html = ""
    modals_html = ""
    start_index = offset + 1
    for idx, r in enumerate(rows, start=start_index):
        row_html, modal_html = build_beneficiary_row_html(r, selected_type, args_dict, page=page, display_index=idx)
        rows_html += row_html
        modals_html += modal_html

    if not rows_html:
        rows_html = f"<tr><td colspan='{len(headers) + (1 if can_bulk_select else 0)}' class='empty-state'>لا توجد نتائج مطابقة لخيارات البحث الحالية.</td></tr>"

    pag_html = ""
    if pages > 1:
        pag_html = "<div class='pagination'>"
        for p in range(1, pages + 1):
            cls = "active" if p == page else ""
            page_query = build_query_string({**args_dict, "page": p})
            pag_html += f"<a class='{cls}' href='?{page_query}'>{p}</a>"
        pag_html += "</div>"

    years_options = "".join([f"<option value='{safe(y)}' {'selected' if args_dict['tawjihi_year']==y else ''}>{safe(y)}</option>" for y in tawjihi_years])
    branches_options = "".join([f"<option value='{safe(x)}' {'selected' if args_dict['tawjihi_branch']==x else ''}>{safe(x)}</option>" for x in tawjihi_branches])
    uni_options = "".join([f"<option value='{safe(x)}' {'selected' if args_dict['university_name']==x else ''}>{safe(x)}</option>" for x in university_names])
    college_options = "".join([f"<option value='{safe(x)}'>{safe(x)}</option>" for x in universities_colleges])
    free_company_options = "".join([f"<option value='{safe(x)}'>{safe(x)}</option>" for x in freelancer_companies])
    free_spec_options = "".join([f"<option value='{safe(x)}'>{safe(x)}</option>" for x in freelancer_specs])
    add_button_html = ""
    if has_permission('add'):
        add_button_html = "<a class='btn btn-secondary' href='#add-beneficiary-modal'><i class='fa-solid fa-user-plus'></i> إضافة مستفيد</a>"
    usage_logs_button_html = f"<a class='btn btn-soft' href='{url_for('usage_logs_page')}'><i class='fa-solid fa-ticket'></i> سجل البطاقات</a>"
    reset_cards_button_html = ""
    if has_permission('reset_weekly_usage'):
        reset_url = url_for('reset_weekly_usage')
        reset_cards_button_html = f"<button class='btn btn-outline' type='button' onclick=\"return resetWeeklyUsageAjax('{reset_url}')\"><i class='fa-solid fa-rotate'></i> تجديد كل البطاقات</button>"

    return locals()
