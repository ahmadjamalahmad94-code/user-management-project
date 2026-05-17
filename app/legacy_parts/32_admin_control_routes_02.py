# Continued split from 32_admin_control_routes.py lines 96-255. Loaded by app.legacy.

@app.route("/admin-control")
@login_required
def admin_control_panel():
    if not (has_permission('manage_bulk_ops') or has_permission('manage_system_cleanup')):
        flash("غير مصرح لك بهذه الصفحة.", "error")
        return redirect(url_for("dashboard"))
    tawjihi_year_options = "".join([f"<option value='{safe(x)}'>{safe(x)}</option>" for x in TAWJIHI_YEARS])
    university_options = "".join([f"<option value='{safe(x)}'>{safe(x)}</option>" for x in UNIVERSITIES_GAZA])
    internet_options = "".join([f"<option value='{safe(x)}'>{safe(x)}</option>" for x in INTERNET_ACCESS_METHOD_OPTIONS])
    time_mode_options = "".join([f"<option value='{safe(x)}'>{safe(x)}</option>" for x in TIME_MODE_OPTIONS])
    freelancer_schedule_options = "".join([f"<option value='{safe(x)}'>{safe(x)}</option>" for x in FREELANCER_SCHEDULE_OPTIONS])
    university_days_options = "".join([f"<option value='{safe(x)}'>{safe(x)}</option>" for x in UNIVERSITY_DAYS_OPTIONS])

    tawjihi_filters = f"""
      <div class='row'>
        <input type='hidden' name='user_type' value='tawjihi'>
        <div><label>سنة التوجيهي</label><select name='tawjihi_year'><option value=''>كل السنوات</option>{tawjihi_year_options}</select></div>
        <div><label>IDs محددة</label><input name='ids' placeholder='مثال: 1,2,3'></div>
      </div>
    """
    tawjihi_edit = f"""
      <form method='POST' action='{url_for('admin_control_apply_update')}'>
        {tawjihi_filters}
        <div class='row'>
          <div><label>التعديل</label><select name='operation'><option value='set_notes'>وضع ملاحظة موحدة</option></select></div>
          <div><label>القيمة الجديدة</label><input name='new_value' placeholder='مثال: تم تحديث البيانات' required></div>
        </div>
        <div class='actions'><button class='btn btn-primary' type='submit'><i class='fa-solid fa-check'></i> تنفيذ التعديل</button></div>
      </form>
    """
    tawjihi_clean = f"""
      <form method='POST' action='{url_for('admin_control_apply_clean')}'>
        {tawjihi_filters}
        <div class='row'>
          <div><label>التنظيف</label><select name='operation'>{build_common_clean_options(include_internet=False, include_times=False)}</select></div>
        </div>
        <div class='actions'><button class='btn btn-outline' type='submit'><i class='fa-solid fa-broom'></i> تنفيذ التنظيف</button></div>
      </form>
    """

    university_filters = f"""
      <div class='row'>
        <input type='hidden' name='user_type' value='university'>
        <div><label>الجامعة</label><select name='university_name'><option value=''>كل الجامعات</option>{university_options}</select></div>
        <div><label>IDs محددة</label><input name='ids' placeholder='مثال: 4,8,9'></div>
      </div>
    """
    university_edit = f"""
      <form method='POST' action='{url_for('admin_control_apply_update')}'>
        {university_filters}
        <div class='row'>
          <div><label>التعديل</label><select name='operation'>
            <option value='set_university_internet_method'>نظام الاتصال بالإنترنت</option>
            <option value='set_university_time_mode'>وضع الوقت</option>
            <option value='set_university_days'>أيام الجامعة</option>
            <option value='set_university_time_from'>وقت من</option>
            <option value='set_university_time_to'>وقت إلى</option>
            <option value='set_notes'>وضع ملاحظة موحدة</option>
          </select></div>
          <div><label>القيمة الجديدة</label><input name='new_value' list='admin-values-university' placeholder='اختر أو اكتب قيمة' required></div>
        </div>
        <datalist id='admin-values-university'>
          {''.join([f"<option value='{safe(x)}'></option>" for x in INTERNET_ACCESS_METHOD_OPTIONS + TIME_MODE_OPTIONS + UNIVERSITY_DAYS_OPTIONS])}
        </datalist>
        <div class='actions'><button class='btn btn-primary' type='submit'><i class='fa-solid fa-check'></i> تنفيذ التعديل</button></div>
      </form>
    """
    university_clean = f"""
      <form method='POST' action='{url_for('admin_control_apply_clean')}'>
        {university_filters}
        <div class='row'>
          <div><label>التنظيف</label><select name='operation'>{build_common_clean_options(include_internet=True, include_times=True)}<option value='clear_days'>مسح الأيام</option></select></div>
        </div>
        <div class='actions'><button class='btn btn-outline' type='submit'><i class='fa-solid fa-broom'></i> تنفيذ التنظيف</button></div>
      </form>
    """

    freelancer_filters = f"""
      <div class='row'>
        <input type='hidden' name='user_type' value='freelancer'>
        <div><label>الشركة</label><input name='freelancer_company' placeholder='فلترة حسب الشركة'></div>
        <div><label>IDs محددة</label><input name='ids' placeholder='مثال: 10,11,12'></div>
      </div>
    """
    freelancer_edit = f"""
      <form method='POST' action='{url_for('admin_control_apply_update')}'>
        {freelancer_filters}
        <div class='row'>
          <div><label>التعديل</label><select name='operation'>
            <option value='set_freelancer_internet_method'>نظام الاتصال بالإنترنت</option>
            <option value='set_freelancer_time_mode'>وضع الوقت</option>
            <option value='set_freelancer_schedule_type'>نوع الدوام</option>
            <option value='set_freelancer_time_from'>وقت من</option>
            <option value='set_freelancer_time_to'>وقت إلى</option>
            <option value='set_notes'>وضع ملاحظة موحدة</option>
          </select></div>
          <div><label>القيمة الجديدة</label><input name='new_value' list='admin-values-freelancer' placeholder='اختر أو اكتب قيمة' required></div>
        </div>
        <datalist id='admin-values-freelancer'>
          {''.join([f"<option value='{safe(x)}'></option>" for x in INTERNET_ACCESS_METHOD_OPTIONS + TIME_MODE_OPTIONS + FREELANCER_SCHEDULE_OPTIONS])}
        </datalist>
        <div class='actions'><button class='btn btn-primary' type='submit'><i class='fa-solid fa-check'></i> تنفيذ التعديل</button></div>
      </form>
    """
    freelancer_clean = f"""
      <form method='POST' action='{url_for('admin_control_apply_clean')}'>
        {freelancer_filters}
        <div class='row'>
          <div><label>التنظيف</label><select name='operation'>{build_common_clean_options(include_internet=True, include_times=True)}<option value='clear_schedule'>مسح نوع الدوام</option></select></div>
        </div>
        <div class='actions'><button class='btn btn-outline' type='submit'><i class='fa-solid fa-broom'></i> تنفيذ التنظيف</button></div>
      </form>
    """

    advanced_clean = f"""
    <div class='card glass-card' style='margin-top:16px'>
      <h3 style='margin-top:0'>تصفير وتنظيف متقدم للنظام</h3>
      <div class='archive-actions-grid'>
        <div class='archive-action-card archive-card-orange'>
          <div class='icon'><i class='fa-solid fa-file-lines'></i></div>
          <h4>تنظيف السجلات التشغيلية</h4>
          <p>يمسح سجل البطاقات الحالي والأرشيف وسجل العمليات فقط.</p>
          <form method='POST' action='{url_for('admin_control_system_reset')}' onsubmit="return confirm('سيتم تنظيف السجلات التشغيلية. متابعة؟')">
            <input type='hidden' name='operation' value='truncate_operational'>
            <button class='btn btn-soft' type='submit'>تنظيف السجلات</button>
          </form>
        </div>
        <div class='archive-action-card archive-card-red'>
          <div class='icon'><i class='fa-solid fa-users-slash'></i></div>
          <h4>حذف كل المستفيدين</h4>
          <p>يحذف المستفيدين وكل السجلات المرتبطة بهم فقط.</p>
          <form method='POST' action='{url_for('admin_control_system_reset')}' onsubmit="return confirm('سيتم حذف كل المستفيدين والسجلات المرتبطة. متابعة؟')">
            <input type='hidden' name='operation' value='truncate_beneficiaries_only'>
            <button class='btn btn-danger' type='submit'>حذف المستفيدين</button>
          </form>
        </div>
        <div class='archive-action-card archive-card-blue'>
          <div class='icon'><i class='fa-solid fa-biohazard'></i></div>
          <h4>تصفير النظام</h4>
          <p>يحذف كل بيانات التشغيل ويُبقي الحسابات والصلاحيات فقط.</p>
          <form method='POST' action='{url_for('admin_control_system_reset')}' onsubmit="return confirm('سيتم تصفير النظام بالكامل. متابعة؟')">
            <input type='hidden' name='operation' value='truncate_everything_except_accounts'>
            <button class='btn btn-danger' type='submit'>تصفير النظام</button>
          </form>
        </div>
      </div>
    </div>
    """

    content = f"""
    <div class='hero'><h1>لوحة التحكم المتقدم</h1><p>3 أقسام أساسية: توجيهي، جامعة، فري لانسر. كل قسم فيه تعديل جماعي + تنظيف جماعي بشكل مرتب وواضح.</p></div>
    {admin_section_card('توجيهي', 'fa-solid fa-user-graduate', 'badge-green', tawjihi_filters, tawjihi_edit, tawjihi_clean)}
    <div style='height:16px'></div>
    {admin_section_card('جامعة', 'fa-solid fa-building-columns', 'badge-purple', university_filters, university_edit, university_clean)}
    <div style='height:16px'></div>
    {admin_section_card('فري لانسر', 'fa-solid fa-laptop-code', 'badge-orange', freelancer_filters, freelancer_edit, freelancer_clean)}
    {advanced_clean}
    """
    return render_page("لوحة التحكم المتقدم", content)
