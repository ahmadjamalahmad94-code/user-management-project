# Auto-split from app/legacy.py lines 6458-6808. Loaded by app.legacy.
def admin_target_summary(filters: dict) -> str:
    parts = []
    if filters.get("user_type"):
        parts.append(get_type_label(filters["user_type"]))
    if filters.get("tawjihi_year"):
        parts.append(f"سنة {filters['tawjihi_year']}")
    if filters.get("university_name"):
        parts.append(filters["university_name"])
    if filters.get("freelancer_company"):
        parts.append(filters["freelancer_company"])
    if filters.get("ids"):
        parts.append(f"IDs محددة ({len(filters['ids'])})")
    return " / ".join(parts) if parts else "الكل"

def admin_scope_values(src=None) -> dict:
    src = src or request.form
    ids_raw = clean_csv_value(src.get("ids", ""))
    ids = [int(x) for x in re.split(r"[,\s]+", ids_raw) if x.strip().isdigit()]
    return {
        "user_type": clean_csv_value(src.get("user_type", "")),
        "tawjihi_year": clean_csv_value(src.get("tawjihi_year", "")),
        "university_name": clean_csv_value(src.get("university_name", "")),
        "freelancer_company": clean_csv_value(src.get("freelancer_company", "")),
        "ids": ids,
    }

def build_admin_target_where(filters: dict):
    where = ["1=1"]
    params = []
    if filters.get("user_type"):
        where.append("user_type = %s")
        params.append(filters["user_type"])
    if filters.get("tawjihi_year"):
        where.append("tawjihi_year = %s")
        params.append(filters["tawjihi_year"])
    if filters.get("university_name"):
        where.append("university_name = %s")
        params.append(filters["university_name"])
    if filters.get("freelancer_company"):
        where.append("freelancer_company ILIKE %s")
        params.append(f"%{filters['freelancer_company']}%")
    if filters.get("ids"):
        where.append("id = ANY(%s)")
        params.append(filters["ids"])
    return " AND ".join(where), params

def count_admin_targets(filters: dict) -> int:
    where_sql, params = build_admin_target_where(filters)
    row = query_one(f"SELECT COUNT(*) AS c FROM beneficiaries WHERE {where_sql}", params)
    return int((row or {}).get("c") or 0)

def execute_admin_update(filters: dict, set_sql: str, values: list):
    where_sql, params = build_admin_target_where(filters)
    row = execute_sql(f"UPDATE beneficiaries SET {set_sql} WHERE {where_sql} RETURNING COUNT(*) OVER() AS c", values + params, fetchone=True)
    return int((row or {}).get("c") or 0)

def execute_admin_sql(sql: str, params=None):
    return execute_sql(sql, params or [])

def admin_section_card(title, icon, color_class, filters_html, edit_html, clean_html):
    return f"""
    <div class='card glass-card'>
      <div class='toolbar-card' style='margin-bottom:12px'>
        <div style='display:flex;align-items:center;gap:10px'>
          <div class='menu-icon' style='margin-bottom:0;width:48px;height:48px'><i class='{icon}'></i></div>
          <div><h3 style='margin:0'>{title}</h3><div class='small'>تعديل وتنظيف خاص بهذا القسم فقط.</div></div>
        </div>
        <span class='badge {color_class}'>{title}</span>
      </div>
      <div class='grid-2'>
        <div class='archive-action-card archive-card-blue'>
          <div class='icon'><i class='fa-solid fa-pen-ruler'></i></div>
          <h4>تعديل جماعي</h4>
          <p>اختر الفلتر والقيمة الجديدة ثم نفّذ.</p>
          {edit_html}
        </div>
        <div class='archive-action-card archive-card-orange'>
          <div class='icon'><i class='fa-solid fa-soap'></i></div>
          <h4>تنظيف جماعي</h4>
          <p>امسح الحقول المحددة لهذا القسم فقط.</p>
          {clean_html}
        </div>
      </div>
    </div>
    """

def build_common_clean_options(include_internet=True, include_times=True):
    opts = ["<option value='clear_notes'>مسح الملاحظات</option>", "<option value='clear_phones'>مسح أرقام الجوالات</option>"]
    if include_internet:
        opts.append("<option value='clear_internet_methods'>مسح نظام الاتصال</option>")
    if include_times:
        opts.append("<option value='clear_times'>مسح الوقت</option>")
    opts.append("<option value='reset_weekly_usage'>تصفير العدادات الأسبوعية</option>")
    return "".join(opts)
