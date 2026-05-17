# Continued split from 09_formatting_signup_helpers.py lines 116-180. Loaded by app.legacy.


def _build_summary_note(form_data):
    """يدمج الحقول التي لا تنتمي للـ schema الأساسي في ملاحظة مختصرة."""
    bits = []
    branch = clean_csv_value(form_data.get("tawjihi_branch"))
    if branch:
        bits.append(f"فرع التوجيهي: {branch}")
    college = clean_csv_value(form_data.get("university_college"))
    if college:
        bits.append(f"الكلية: {college}")
    return " | ".join(bits)


def create_beneficiary_signup_request(form_data):
    phone = normalize_phone(form_data.get("phone"))
    first_name = clean_csv_value(form_data.get("first_name"))
    second_name = clean_csv_value(form_data.get("second_name"))
    third_name = clean_csv_value(form_data.get("third_name"))
    fourth_name = clean_csv_value(form_data.get("fourth_name"))
    user_type = clean_csv_value(form_data.get("track"))
    full_name = full_name_from_parts(first_name, second_name, third_name, fourth_name)
    search_name = normalize_search_ar(full_name)

    params = [
        phone,
        first_name,
        second_name,
        third_name,
        fourth_name,
        full_name,
        search_name,
        user_type,
        clean_csv_value(form_data.get("tawjihi_year")),
        clean_csv_value(form_data.get("university_name")),
        clean_csv_value(form_data.get("university_major")),
        clean_csv_value(form_data.get("university_number")),
        clean_csv_value(form_data.get("freelancer_type")),
        clean_csv_value(form_data.get("freelancer_specialization")),
        clean_csv_value(form_data.get("freelancer_field")),
        clean_csv_value(form_data.get("company_proof")),
        clean_csv_value(form_data.get("company_name")),
        clean_csv_value(form_data.get("summary_note") or _build_summary_note(form_data)),
        clean_csv_value(form_data.get("notes")),
    ]

    row = execute_sql(
        """
        INSERT INTO beneficiary_signup_requests (
            phone, first_name, second_name, third_name, fourth_name,
            full_name, search_name, user_type, tawjihi_year,
            university_name, university_major, university_number,
            freelancer_type, freelancer_specialization, freelancer_field,
            company_proof, company_name, summary_note, notes
        ) VALUES (
            %s,%s,%s,%s,%s,
            %s,%s,%s,%s,
            %s,%s,%s,
            %s,%s,%s,
            %s,%s,%s,%s
        )
        RETURNING id
        """,
        params,
        fetchone=True,
    )
    if isinstance(row, dict):
        return row.get("id")
    return row["id"] if row else None


CARD_DURATION_OPTIONS = [
    {"minutes": 30, "label": "نصف ساعة"},
    {"minutes": 60, "label": "ساعة"},
    {"minutes": 120, "label": "ساعتين"},
    {"minutes": 180, "label": "3 ساعات"},
    {"minutes": 240, "label": "4 ساعات"},
]
