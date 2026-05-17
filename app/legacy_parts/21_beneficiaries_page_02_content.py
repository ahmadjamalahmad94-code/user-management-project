# Beneficiaries page HTML extracted from 21_beneficiaries_page.py. Loaded by app.legacy.

def _beneficiaries_page_content(context):
    tabs_html = context['tabs_html']
    args_dict = context['args_dict']
    years_options = context['years_options']
    branches_options = context['branches_options']
    uni_options = context['uni_options']
    selected_type = context['selected_type']
    college_options = context['college_options']
    free_company_options = context['free_company_options']
    free_spec_options = context['free_spec_options']
    add_button_html = context['add_button_html']
    usage_logs_button_html = context['usage_logs_button_html']
    reset_cards_button_html = context['reset_cards_button_html']
    metric_html = context['metric_html']
    thead = context['thead']
    rows_html = context['rows_html']
    modals_html = context['modals_html']
    pag_html = context['pag_html']

    content = f"""
    <div class="hero">
      <h1>إدارة المستفيدين المتقدمة</h1>
      <p>تبويبات حسب النوع، بحث شامل، فلاتر متخصصة، ترتيب أعمدة، وتعديل منبثق بدون الخروج من الصفحة.</p>
    </div>

    <div class="tabs">{tabs_html}</div>

    <div class="card">
      <div class="filter-box">
        <form method="GET">
          <div class="row">
            <div><label>بحث عام</label><input name="q" value="{safe(args_dict['q'])}" placeholder="اسم، جوال، جامعة، تخصص، شركة، سنة..."></div>
            <div>
              <label>النوع</label>
              <select name="user_type">
                <option value="">الكل</option>
                <option value="tawjihi" {"selected" if selected_type=="tawjihi" else ""}>توجيهي</option>
                <option value="university" {"selected" if selected_type=="university" else ""}>جامعة</option>
                <option value="freelancer" {"selected" if selected_type=="freelancer" else ""}>فري لانسر</option>
              </select>
            </div>
            <div>
              <label>الترتيب</label>
              <select name="sort_by">
                <option value="id" {"selected" if args_dict['sort_by']=="id" else ""}>ID</option>
                <option value="full_name" {"selected" if args_dict['sort_by']=="full_name" else ""}>الاسم</option>
                <option value="phone" {"selected" if args_dict['sort_by']=="phone" else ""}>الجوال</option>
                <option value="weekly_usage_count" {"selected" if args_dict['sort_by']=="weekly_usage_count" else ""}>الاستخدام</option>
                <option value="created_at" {"selected" if args_dict['sort_by']=="created_at" else ""}>تاريخ الإضافة</option>
              </select>
            </div>
            <div>
              <label>اتجاه الترتيب</label>
              <select name="sort_order">
                <option value="desc" {"selected" if args_dict['sort_order']=="desc" else ""}>تنازلي</option>
                <option value="asc" {"selected" if args_dict['sort_order']=="asc" else ""}>تصاعدي</option>
              </select>
            </div>
          </div>

          <details class="advanced-filters" {"open" if any([args_dict['tawjihi_year'], args_dict['tawjihi_branch'], args_dict['university_name'], args_dict['university_college'], args_dict['university_specialization'], args_dict['freelancer_specialization'], args_dict['freelancer_company'], args_dict['internet_method']]) else ""}>
            <summary><i class="fa-solid fa-sliders"></i> فلاتر متقدمة</summary>
            <div class="row">
              <div>
                <label>سنة التوجيهي</label>
                <select name="tawjihi_year"><option value="">الكل</option>{years_options}</select>
              </div>
              <div>
                <label>فرع التوجيهي</label>
                <select name="tawjihi_branch"><option value="">الكل</option>{branches_options}</select>
              </div>
              <div>
                <label>الجامعة</label>
                <select name="university_name"><option value="">الكل</option>{uni_options}</select>
              </div>
              <div><label>الكلية</label><input name="university_college" list="colleges-list" value="{safe(args_dict['university_college'])}" placeholder="ابحث حسب الكلية"></div>
              <div><label>التخصص الجامعي</label><input name="university_specialization" value="{safe(args_dict['university_specialization'])}" placeholder="مثال: هندسة برمجيات"></div>
              <div><label>تخصص الفري لانسر</label><input name="freelancer_specialization" list="freelancer-specs" value="{safe(args_dict['freelancer_specialization'])}" placeholder="مثال: تصميم جرافيك"></div>
              <div><label>شركة الفري لانسر</label><input name="freelancer_company" list="freelancer-companies" value="{safe(args_dict['freelancer_company'])}" placeholder="مثال: Upwork"></div>
              <div>
                <label>طريقة الإنترنت</label>
                <select name="internet_method">
                  <option value="">الكل</option>
                  <option value="cards" {"selected" if args_dict['internet_method']=="cards" else ""}>نظام البطاقات / محدود</option>
                  <option value="username" {"selected" if args_dict['internet_method']=="username" else ""}>يمتلك اسم مستخدم</option>
                </select>
              </div>
            </div>
          </details>

          <datalist id="colleges-list">{college_options}</datalist>
          <datalist id="freelancer-companies">{free_company_options}</datalist>
          <datalist id="freelancer-specs">{free_spec_options}</datalist>

          <div class="actions" style="margin-top:4px">
            <button class="btn btn-primary" type="submit"><i class="fa-solid fa-magnifying-glass"></i> تطبيق البحث</button>
            <a class="btn btn-soft" href="{url_for('beneficiaries_page')}"><i class="fa-solid fa-rotate-left"></i> إعادة ضبط</a>
            {add_button_html}
            {usage_logs_button_html}
            {reset_cards_button_html}
          </div>
        </form>
      </div>

      <div class="metric-grid" style="margin-top:16px">{metric_html}</div>
    </div>

    <div class="card" style="margin-top:14px">
      <div class='bulk-toolbar'>
        <span class='selected-count'>المحدد: <strong id='selected-count'>0</strong></span>
        {"<button class='btn btn-soft btn-icon' type='button' onclick='return submitBulkExport()' title='تصدير المحدد'><i class='fa-solid fa-file-export'></i></button>" if has_permission('export') else ""}
        {"<button class='btn btn-danger btn-icon' type='button' onclick='return submitBulkDelete()' title='حذف المحدد'><i class='fa-solid fa-trash'></i></button>" if has_permission('delete') else ""}
      </div>
      <form id='bulk-delete-form' method='POST' action='{url_for('bulk_delete_beneficiaries')}' style='display:none'><input type='hidden' name='ids' value=''></form>
      <form id='bulk-export-form' method='POST' action='{url_for('export_selected_beneficiaries')}' style='display:none'><input type='hidden' name='ids' value=''></form>
      <div class="table-wrap">
        <table>
          <thead>{thead}</thead>
          <tbody>{rows_html}</tbody>
        </table>
      </div>
      {pag_html}
    </div>

    {modals_html}
    {build_add_beneficiary_modal(selected_type or 'tawjihi')}
    """

    return content
