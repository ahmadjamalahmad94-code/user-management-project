# Auto-split from app/legacy.py lines 9586-9682. Loaded by app.legacy.
def _clean_user_register_v2():
    if request.method == "POST":
        flash("تم استلام طلب الاشتراك داخليًا. ستقوم الإدارة بمراجعة البيانات وتجهيز الحساب المناسب عند الاعتماد.", "info")
        return redirect(url_for("user_register"))
    content = """
    <section class="portal-auth-hero">
      <div>
        <span class="badge badge-blue">بوابة المشتركين</span>
        <h1>تسجيل اشتراك جديد</h1>
        <p>املأ البيانات الأساسية حسب مجالك، وسنجهز لك نوع الحساب المناسب: توجيهي، جامعة، أو فري لانسر.</p>
      </div>
      <div class="portal-feature-list">
        <div><i class="fa-solid fa-user-check"></i><span>نموذج واضح ومنظم</span></div>
        <div><i class="fa-solid fa-layer-group"></i><span>حقول تختلف حسب المجال</span></div>
        <div><i class="fa-solid fa-clipboard-check"></i><span>واجهة ناعمة قابلة للتطوير لاحقًا</span></div>
      </div>
    </section>
    <div class="portal-panel">
      <form method="POST" id="portal-register-form">
        <div class="grid grid-2">
          <div><label>رقم الجوال</label><input name="phone" placeholder="05xxxxxxxx" required></div>
          <div><label>المجال</label><select name="track" id="portal-track" required onchange="togglePortalTrackFields()"><option value="">اختر المجال</option><option value="tawjihi">توجيهي</option><option value="university">جامعة</option><option value="freelancer">فري لانسر</option></select></div>
          <div><label>الاسم الأول</label><input name="first_name" required></div>
          <div><label>الاسم الثاني</label><input name="second_name" required></div>
          <div><label>الاسم الثالث</label><input name="third_name" required></div>
          <div><label>الاسم الرابع</label><input name="fourth_name" required></div>
        </div>

        <div id="track-tawjihi" class="form-section" style="margin-top:16px">
          <div class="grid grid-2">
            <div><label>سنة التوجيهي</label><select name="tawjihi_year"><option value="">اختر السنة</option><option value="2007">2007</option><option value="2008">2008</option><option value="2009">2009</option><option value="2010">2010</option></select></div>
          </div>
        </div>

        <div id="track-university" class="form-section" style="margin-top:16px">
          <div class="grid grid-2">
            <div><label>اسم الجامعة</label><input name="university_name"></div>
            <div><label>التخصص</label><input name="university_major"></div>
            <div><label>الرقم الجامعي</label><input name="university_number"></div>
          </div>
        </div>

        <div id="track-freelancer" class="form-section" style="margin-top:16px">
          <div class="grid grid-2">
            <div><label>نوع العمل</label><select name="freelancer_type" id="freelancer-type" onchange="toggleFreelancerContractFields()"><option value="">اختر النوع</option><option value="independent">عمل حر</option><option value="company_contract">عقد مع شركة</option></select></div>
            <div><label>التخصص</label><input name="freelancer_specialization"></div>
            <div class="grid-col-span-2"><label>المجال</label><input name="freelancer_field" placeholder="مثال: تصميم، برمجة، تسويق، مونتاج..."></div>
          </div>
          <div id="freelancer-contract-fields" class="form-section" style="margin-top:16px">
            <div class="info-note">إذا كان لديك عقد مع شركة، هل يمكن تقديم صورة من عقد العمل أو بريد رسمي من الشركة؟</div>
            <div class="grid grid-2" style="margin-top:12px">
              <div><label>إثبات من الشركة</label><select name="company_proof"><option value="">اختر</option><option value="contract_image">صورة من عقد العمل</option><option value="company_email">بريد من الشركة</option><option value="other">إثبات آخر</option></select></div>
              <div><label>اسم الشركة</label><input name="company_name"></div>
            </div>
          </div>
        </div>

        <div class="grid grid-2" style="margin-top:16px">
          <div><label>نوع الاستفادة المطلوبة</label><select name="access_mode"><option value="username">يوزر إنترنت</option><option value="cards">بطاقات استخدام</option></select></div>
          <div><label>ملاحظات مختصرة</label><input name="summary_note" placeholder="أي ملاحظة سريعة للإدارة"></div>
          <div class="grid-col-span-2"><label>ملاحظات</label><textarea name="notes" class="notes-box" placeholder="أي بيانات تساعد الإدارة على تجهيز الحساب المناسب"></textarea></div>
        </div>
        <div class="actions" style="margin-top:16px">
          <button class="btn btn-primary" type="submit">إرسال طلب الاشتراك</button>
          <a class="btn btn-soft" href="/user/login">لديك حساب؟ تسجيل الدخول</a>
        </div>
      </form>
    </div>
    <script>
    function togglePortalTrackFields(){
      var track = document.getElementById('portal-track');
      var value = track ? track.value : '';
      ['track-tawjihi','track-university','track-freelancer'].forEach(function(id){
        var el = document.getElementById(id);
        if(el){ el.classList.remove('active'); }
      });
      if(value){
        var section = document.getElementById('track-' + value);
        if(section){ section.classList.add('active'); }
      }
    }
    function toggleFreelancerContractFields(){
      var box = document.getElementById('freelancer-contract-fields');
      var type = document.getElementById('freelancer-type');
      if(!box || !type) return;
      box.classList.toggle('active', type.value === 'company_contract');
    }
    document.addEventListener('DOMContentLoaded', function(){
      togglePortalTrackFields();
      toggleFreelancerContractFields();
    });
    </script>
    """
    return render_user_page("تسجيل اشتراك", content)


app.view_functions["user_register"] = _clean_user_register_v2
