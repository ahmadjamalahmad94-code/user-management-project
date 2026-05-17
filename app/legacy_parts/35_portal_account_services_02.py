# Continued split from 35_portal_account_services.py lines 145-242. Loaded by app.legacy.


def render_internet_request_form():
    beneficiaries = query_all("SELECT id, full_name, phone FROM beneficiaries ORDER BY id DESC LIMIT 500")
    options = "".join(
        f"<option value='{r['id']}'>{safe(r.get('full_name'))} - {safe(r.get('phone'))}</option>"
        for r in beneficiaries
    )
    content = f"""
    <div class='hero'>
      <div>
        <h1>طلب خدمة إنترنت</h1>
        <p>سجل طلبًا مجانيًا للمستفيد، وسيظهر للإدارة للمراجعة ثم التنفيذ عند الموافقة.</p>
      </div>
      <div class='actions'>
        <a class='btn btn-soft' href='{url_for("internet_my_requests_page")}'>طلباتي</a>
        <a class='btn btn-secondary' href='{url_for("internet_my_access_page")}'>الوصول المرتبط</a>
      </div>
    </div>
    <div class='grid grid-3' style='margin-bottom:16px'>
      <div class='stat'><div class='icon'><i class='fa-solid fa-user-plus'></i></div><strong>طلب خدمة إنترنت</strong><div class='muted'>إنشاء مستخدم جديد للمستفيد.</div></div>
      <div class='stat'><div class='icon'><i class='fa-solid fa-ticket'></i></div><strong>طلب بطاقة استخدام</strong><div class='muted'>إصدار بطاقة مجانية من المركز.</div></div>
      <div class='stat'><div class='icon'><i class='fa-solid fa-gauge-high'></i></div><strong>رفع سرعة مؤقت</strong><div class='muted'>تعديل مؤقت للبروفايل مع استرجاع لاحق.</div></div>
    </div>
    <div class='card'>
      <form method='POST'>
        <div class='grid grid-2'>
          <div><label>المستفيد</label><select name='beneficiary_id' required>{options}</select></div>
          <div><label>نوع الطلب</label><select name='request_type' required>
            <option value='create_user'>طلب خدمة إنترنت</option>
            <option value='request_card'>طلب بطاقة استخدام</option>
            <option value='temporary_speed_upgrade'>طلب رفع سرعة مؤقت</option>
            <option value='add_time'>طلب إضافة وقت</option>
            <option value='add_quota'>طلب إضافة كوتة</option>
            <option value='update_mac'>طلب تحديث MAC</option>
            <option value='reset_password'>طلب إعادة تعيين كلمة المرور</option>
            <option value='other'>طلب آخر</option>
          </select></div>
          <div><label>اسم المستخدم الخارجي</label><input name='external_username' placeholder='existing.username'></div>
          <div><label>اسم المستخدم المطلوب عند الإنشاء</label><input name='desired_username' placeholder='new.username'></div>
          <div><label>كلمة مرور أولية / جديدة</label><input name='desired_password' placeholder='اختياري'></div>
          <div><label>رقم / اسم البروفايل</label><div class='grid grid-2'><input name='profile_id' placeholder='profile_id'><input name='profile_name' placeholder='profile_name'></div></div>
          <div><label>عدد البطاقات</label><input name='card_count' type='number' min='1' value='1'></div>
          <div><label>مدة رفع السرعة بالدقائق</label><input name='duration_minutes' type='number' min='1' value='60'></div>
          <div><label>إضافة وقت</label><div class='grid grid-2'><input name='time_amount' type='number' min='1' placeholder='القيمة'><select name='time_unit'><option value='minutes'>دقائق</option><option value='hours'>ساعات</option><option value='days'>أيام</option></select></div></div>
          <div><label>إضافة كوتة</label><div class='grid grid-3'><input name='quota_amount_mb' type='number' min='1' placeholder='MB إجمالي'><input name='upload_quota_mb' type='number' min='0' placeholder='رفع'><input name='download_quota_mb' type='number' min='0' placeholder='تنزيل'></div></div>
          <div><label>عنوان MAC</label><input name='mac_address' placeholder='AA:BB:CC:DD:EE:FF'></div>
          <div><label>ملاحظات</label><textarea name='notes' class='notes-box' placeholder='تفاصيل إضافية أو مبرر الطلب'></textarea></div>
        </div>
        <div class='actions' style='margin-top:16px'>
          <button class='btn btn-primary' type='submit'><i class='fa-solid fa-paper-plane'></i> إرسال الطلب</button>
          <a class='btn btn-soft' href='{url_for("internet_my_requests_page")}'>عرض السجل</a>
        </div>
      </form>
    </div>
    """
    return render_page("طلب خدمة إنترنت", content)


def render_user_request_form():
    beneficiary = get_current_portal_beneficiary()
    content = f"""
    <div class='hero'>
      <div>
        <h1>طلب خدمة إنترنت</h1>
        <p>يمكنك من هنا إرسال طلبات الخدمات المجانية الخاصة بحسابك فقط، وستصل للإدارة للمراجعة.</p>
      </div>
    </div>
    <div class='card'>
      <div class='small' style='margin-bottom:12px'>المستفيد الحالي: {safe(beneficiary.get('full_name'))} - {safe(beneficiary.get('phone'))}</div>
      <form method='POST'>
        <div class='grid grid-2'>
          <div><label>نوع الطلب</label><select name='request_type' required>
            <option value='create_user'>طلب خدمة إنترنت</option>
            <option value='request_card'>طلب بطاقة استخدام</option>
            <option value='temporary_speed_upgrade'>طلب رفع سرعة مؤقت</option>
            <option value='add_time'>طلب إضافة وقت</option>
            <option value='add_quota'>طلب إضافة كوتة</option>
            <option value='update_mac'>طلب تحديث MAC</option>
            <option value='reset_password'>طلب إعادة تعيين كلمة المرور</option>
          </select></div>
          <div><label>اسم المستخدم الخارجي الحالي أو المطلوب</label><input name='external_username'></div>
          <div><label>اسم مستخدم جديد عند الإنشاء</label><input name='desired_username'></div>
          <div><label>رقم / اسم البروفايل</label><div class='grid grid-2'><input name='profile_id' placeholder='profile_id'><input name='profile_name' placeholder='profile_name'></div></div>
          <div><label>عدد البطاقات</label><input name='card_count' type='number' min='1' value='1'></div>
          <div><label>مدة رفع السرعة بالدقائق</label><input name='duration_minutes' type='number' min='1' value='60'></div>
          <div><label>إضافة وقت</label><div class='grid grid-2'><input name='time_amount' type='number' min='1'><select name='time_unit'><option value='minutes'>دقائق</option><option value='hours'>ساعات</option><option value='days'>أيام</option></select></div></div>
          <div><label>إضافة كوتة</label><div class='grid grid-3'><input name='quota_amount_mb' type='number' min='1' placeholder='إجمالي'><input name='upload_quota_mb' type='number' min='0' placeholder='رفع'><input name='download_quota_mb' type='number' min='0' placeholder='تنزيل'></div></div>
          <div><label>عنوان MAC</label><input name='mac_address' placeholder='AA:BB:CC:DD:EE:FF'></div>
          <div><label>ملاحظات</label><textarea name='notes' class='notes-box' placeholder='تفاصيل إضافية أو مبرر الطلب'></textarea></div>
        </div>
        <div class='actions' style='margin-top:16px'>
          <button class='btn btn-primary' type='submit'><i class='fa-solid fa-paper-plane'></i> إرسال الطلب</button>
        </div>
      </form>
    </div>
    """
    return render_user_page("طلب خدمة إنترنت", content)
