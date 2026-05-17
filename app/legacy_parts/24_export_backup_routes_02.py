# Continued split from 24_export_backup_routes.py lines 51-198. Loaded by app.legacy.


@app.route("/export_csv")
@login_required
@permission_required("export")
def export_csv():
    args_dict = build_request_args_dict()
    filters, params = build_beneficiary_filters(args_dict)
    where = " AND ".join(filters)
    rows = query_all(f"SELECT * FROM beneficiaries WHERE {where} ORDER BY id DESC", params)

    export_columns = [
        (None, "#"),
        ("user_type", "نوع المستفيد"),
        ("first_name", "الاسم الأول"),
        ("second_name", "الاسم الثاني"),
        ("third_name", "الاسم الثالث"),
        ("fourth_name", "الاسم الرابع"),
        ("full_name", "الاسم الكامل"),
        ("search_name", "اسم البحث"),
        ("phone", "رقم الجوال"),
        ("tawjihi_year", "سنة التوجيهي"),
        ("tawjihi_branch", "فرع التوجيهي"),
        ("freelancer_specialization", "تخصص الفري لانسر"),
        ("freelancer_company", "شركة الفري لانسر"),
        ("freelancer_schedule_type", "نوع دوام الفري لانسر"),
        ("freelancer_internet_method", "طريقة إنترنت الفري لانسر"),
        ("freelancer_time_mode", "وضع وقت الفري لانسر"),
        ("freelancer_time_from", "وقت الفري لانسر من"),
        ("freelancer_time_to", "وقت الفري لانسر إلى"),
        ("university_name", "الجامعة"),
        ("university_college", "الكلية"),
        ("university_specialization", "التخصص الجامعي"),
        ("university_days", "أيام الجامعة"),
        ("university_internet_method", "طريقة إنترنت الجامعة"),
        ("university_time_mode", "وضع وقت الجامعة"),
        ("university_time_from", "وقت الجامعة من"),
        ("university_time_to", "وقت الجامعة إلى"),
        ("weekly_usage_count", "عدد الاستخدام الأسبوعي"),
        ("weekly_usage_week_start", "بداية الأسبوع"),
        ("created_at", "تاريخ الإنشاء"),
    ]

    def excel_value(value):
        if value is None:
            return ""
        return str(value)

    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "المستفيدون"

    title_fill = PatternFill(fill_type="solid", fgColor="123B6D")
    title_font = Font(color="FFFFFF", bold=True)
    header_fill = PatternFill(fill_type="solid", fgColor="EAF3FB")
    header_font = Font(bold=True, color="123B6D")
    center_alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    top_alignment = Alignment(vertical="top", wrap_text=True)
    thin_side = Side(style="thin", color="DCE8F3")
    thin_border = Border(left=thin_side, right=thin_side, top=thin_side, bottom=thin_side)

    # report title
    report_title = "تقرير المستفيدين المفلتر - Hobe Hub" if any(v for k, v in args_dict.items() if k not in {"sort_by", "sort_order"}) else "تقرير المستفيدين - Hobe Hub"
    sheet.merge_cells(start_row=1, start_column=1, end_row=1, end_column=len(export_columns))
    title_cell = sheet.cell(row=1, column=1, value=report_title)
    title_cell.fill = title_fill
    title_cell.font = Font(color="FFFFFF", bold=True, size=14)
    title_cell.alignment = center_alignment
    sheet.row_dimensions[1].height = 24

    # headers
    for col_idx, (_, header_label) in enumerate(export_columns, start=1):
        cell = sheet.cell(row=2, column=col_idx, value=header_label)
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = center_alignment
        cell.border = thin_border

    # data rows
    for row_idx, row in enumerate(rows, start=3):
        row_dict = dict(row)
        for col_idx, (field_name, _) in enumerate(export_columns, start=1):
            value = row_dict.get(field_name, "")
            cell = sheet.cell(row=row_idx, column=col_idx, value=excel_value(value))
            cell.border = thin_border
            if field_name in {"id", "weekly_usage_count"}:
                cell.alignment = center_alignment
            else:
                cell.alignment = top_alignment

    # freeze, filter, widths
    sheet.freeze_panes = "A3"
    sheet.auto_filter.ref = f"A2:{get_column_letter(len(export_columns))}{max(sheet.max_row, 2)}"

    width_overrides = {
        "A": 10, "B": 16, "C": 18, "D": 18, "E": 18, "F": 18, "G": 28, "H": 24, "I": 18,
        "J": 16, "K": 16, "L": 24, "M": 24, "N": 22, "O": 22, "P": 20, "Q": 16, "R": 16,
        "S": 24, "T": 24, "U": 24, "V": 18, "W": 22, "X": 20, "Y": 16, "Z": 16, "AA": 16,
        "AB": 18, "AC": 22
    }
    for col_idx in range(1, len(export_columns) + 1):
        col_letter = get_column_letter(col_idx)
        max_length = 0
        for row_idx in range(2, sheet.max_row + 1):
            cell = sheet.cell(row=row_idx, column=col_idx)
            try:
                cell_len = len(str(cell.value)) if cell.value is not None else 0
                if cell_len > max_length:
                    max_length = cell_len
            except Exception:
                pass
        sheet.column_dimensions[col_letter].width = width_overrides.get(col_letter, min(max(max_length + 2, 12), 35))

    output = io.BytesIO()
    workbook.save(output)
    output.seek(0)

    log_action("export", "beneficiary", None, "تصدير Excel XLSX")
    resp = Response(
        output.getvalue(),
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
    resp.headers["Content-Disposition"] = "attachment; filename=beneficiaries_export.xlsx"
    return resp


@app.route("/backup_sql")
@login_required
@permission_required("backup")
def backup_sql():
    rows = query_all("SELECT * FROM beneficiaries ORDER BY id")
    lines = []
    for r in rows:
        cols = []
        vals = []
        for k, v in r.items():
            cols.append(k)
            if v is None:
                vals.append("NULL")
            else:
                sval = str(v).replace("'", "''")
                vals.append(f"'{sval}'")
        lines.append(f"INSERT INTO beneficiaries ({', '.join(cols)}) VALUES ({', '.join(vals)});")
    data = "\n".join(lines)
    log_action("backup", "beneficiary", None, "Backup SQL")
    resp = Response(data, mimetype="application/sql")
    resp.headers["Content-Disposition"] = "attachment; filename=beneficiaries_backup.sql"
    return resp
