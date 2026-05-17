# Auto-split from app/legacy.py lines 6209-6455. Loaded by app.legacy.
def render_user_page(title, content):
    beneficiary = get_current_portal_beneficiary() if session.get("portal_type") == "beneficiary" else None
    return render_template_string(
        USER_BASE_TEMPLATE,
        title=title,
        content=content,
        portal_access_mode=get_beneficiary_access_mode(beneficiary),
        portal_access_label=get_beneficiary_access_label(beneficiary),
    )

def truncate_note_words(value, limit=3):
    text = clean_csv_value(value)
    if not text:
        return "-", False, ""
    words = text.split()
    if len(words) <= limit:
        safe_text = safe(text)
        return safe_text, False, safe_text
    return safe(" ".join(words[:limit]) + " ..."), True, safe(text)


def build_add_beneficiary_modal(selected_type='tawjihi'):
    selected_type = clean_csv_value(selected_type) or 'tawjihi'
    modal_form = format_modal_fields(
        {'user_type': selected_type},
        action=url_for('add_beneficiary_page'),
        scope_id='add-beneficiary-scope',
        submit_label='حفظ المستفيد',
        show_type_selector=False,
        fixed_user_type=selected_type,
    )
    modal_form = re.sub(
        r'<div>\s*<label>النوع</label>\s*<input value=".*?" disabled>\s*<input type="hidden" name="user_type" value=".*?">\s*</div>',
        '',
        modal_form,
        count=1,
        flags=re.DOTALL,
    )
    tabs_html = (
        "<div class='type-tabs'>"
        + '<button type=\'button\' class=\'type-tab {cls}\' data-value=\'tawjihi\' onclick="return setBeneficiaryType(\'add-beneficiary-scope\',\'tawjihi\')">توجيهي</button>'.format(cls=('active' if selected_type == 'tawjihi' else ''))
        + '<button type=\'button\' class=\'type-tab {cls}\' data-value=\'university\' onclick="return setBeneficiaryType(\'add-beneficiary-scope\',\'university\')">جامعة</button>'.format(cls=('active' if selected_type == 'university' else ''))
        + '<button type=\'button\' class=\'type-tab {cls}\' data-value=\'freelancer\' onclick="return setBeneficiaryType(\'add-beneficiary-scope\',\'freelancer\')">فري لانسر</button>'.format(cls=('active' if selected_type == 'freelancer' else ''))
        + '</div>'
        + f"<input type='hidden' name='user_type' value='{selected_type}'>"
    )
    modal_form = modal_form.replace(
        '<div id="add-beneficiary-scope" data-beneficiary-scope="1">',
        '<div id="add-beneficiary-scope" data-beneficiary-scope="1">' + tabs_html,
        1,
    )
    modal_form = modal_form.replace('<form method="POST" action="', '<form method="POST" onsubmit="return submitBeneficiaryAdd(this)" action="', 1)
    return f'''
    <div id="add-beneficiary-modal" class="modal">
      <div class="modal-card">
        <a href="#!" class="modal-close">×</a>
        <div class="hero" style="margin-bottom:8px"><h1>إضافة مستفيد</h1><p>اختر النوع من التبويبات أعلى النموذج ثم احفظ بدون إعادة تحميل الصفحة.</p></div>
        {modal_form}
      </div>
    </div>
    '''

def build_beneficiary_row_html(r, selected_type, args_dict, page=1, display_index=None):
    usage_label, limited, count = get_usage_label(r)
    current_qs = build_query_string({**args_dict, "page": page})
    row_class = f"row-type-{safe(r.get('user_type'))}"
    if limited and count >= 3:
        row_class += " row-complete"
    modal_id = f"edit-{r['id']}"
    note_modal_id = f"note-{r['id']}"
    actions = []
    modal_html = ""
    if has_permission("edit"):
        edit_action = f"{url_for('edit_beneficiary_page', beneficiary_id=r['id'])}?current_user_type={selected_type}"
        modal_body = format_modal_fields(
            r,
            action=edit_action,
            scope_id=f"scope-{r['id']}",
            submit_label="حفظ التعديلات",
            show_type_selector=True,
        )
        edit_onsubmit = f"<form method=\"POST\" onsubmit=\"return submitBeneficiaryEdit(this, {r['id']}, '{modal_id}')\" action=\""
        modal_body = modal_body.replace('<form method="POST" action="', edit_onsubmit, 1)
        modal_html = f"""
        <div id="{modal_id}" class="modal">
          <div class="modal-card">
            <a href="#!" class="modal-close">×</a>
            <div class="hero" style="margin-bottom:8px"><h1>تعديل المستفيد #{r['id']}</h1><p>{safe(r.get('full_name'))}</p></div>
            {modal_body}
          </div>
        </div>
        """
        actions.append(f"<a class='btn btn-secondary btn-icon' href='#{modal_id}' title='تعديل'><i class='fa-solid fa-pen'></i></a>")
    if has_permission("delete"):
        delete_url = url_for('delete_beneficiary', beneficiary_id=r['id'])
        actions.append(f"<form class='inline-form' method='POST' action='{delete_url}' onsubmit=\"return confirm('هل أنت متأكد من الحذف؟')\"><button class='btn btn-danger btn-icon' type='submit' title='حذف'><i class='fa-solid fa-trash'></i></button></form>")
    if has_permission("usage_counter") and limited and count < 3:
        usage_url = f"{url_for('add_usage', beneficiary_id=r['id'])}?{current_qs}"
        actions.append(f"<button class='btn btn-accent btn-icon' type='button' onclick=\"return openGlobalUsageModal({r['id']}, '{usage_url}')\" title='+1 بطاقة'><i class='fa-solid fa-plus'></i></button>")
    type_html = f"<span class='type-badge {get_type_css(r.get('user_type'))}'>{get_type_label(r.get('user_type'))}</span>"
    added_by = safe(r.get('added_by_username')) or '-'
    created_at = format_dt_short(r.get('created_at'))
    note_preview, has_note_modal, note_full = truncate_note_words(r.get('notes'))
    notes_html = note_preview
    if has_note_modal:
        notes_html = f"<span class='note-preview'><span class='note-text'>{note_preview}</span><a class='btn btn-soft btn-icon' href='#{note_modal_id}' title='عرض الملاحظة'><i class='fa-solid fa-eye'></i></a></span>"
        modal_html += f"""
        <div id="{note_modal_id}" class="modal">
          <div class="modal-card" style="width:min(650px,100%)">
            <a href="#!" class="modal-close">×</a>
            <div class="hero" style="margin-bottom:8px"><h1>ملاحظة المستفيد</h1><p>{safe(r.get('full_name'))}</p></div>
            <div class="card"><div class='cell-wrap' style='max-width:none'>{note_full}</div></div>
          </div>
        </div>
        """
    display_no = safe(display_index if display_index is not None else r.get('id'))
    if selected_type == "tawjihi":
        row_cells = [display_no, safe(r['full_name']), safe(r['phone']), safe(r['tawjihi_year']), safe(r['tawjihi_branch']), usage_label, added_by, created_at, notes_html, " ".join(actions) if actions else "-"]
        usage_idx = 5
    elif selected_type == "university":
        row_cells = [display_no, safe(r['full_name']), safe(r['phone']), safe(r['university_name']), safe(r['university_college']), safe(r['university_specialization']), usage_label, added_by, created_at, notes_html, " ".join(actions) if actions else "-"]
        usage_idx = 6
    elif selected_type == "freelancer":
        row_cells = [display_no, safe(r['full_name']), safe(r['phone']), safe(r['freelancer_specialization']), safe(r['freelancer_company']), usage_label, added_by, created_at, notes_html, " ".join(actions) if actions else "-"]
        usage_idx = 5
    else:
        row_cells = [display_no, safe(r['full_name']), safe(r['phone']), type_html, usage_label, added_by, created_at, notes_html, " ".join(actions) if actions else "-"]
        usage_idx = 4
    cells = []
    for i, cell in enumerate(row_cells):
        extra = ' usage-cell' if i == usage_idx else ''
        cells.append(f"<td class='cell-wrap{extra}'>{cell}</td>")
    can_bulk_select = has_permission('delete') or has_permission('export')
    if can_bulk_select:
        cells.append(f"<td class='checkbox-cell'><input class='row-select' type='checkbox' value='{r['id']}' onchange='updateBulkSelectedCount()'></td>")
    row_html = f"<tr id='beneficiary-row-{r['id']}' class='{row_class}' data-limited={'1' if limited else '0'}>" + ''.join(cells) + "</tr>"
    return row_html, modal_html
