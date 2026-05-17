# Auto-split from app/legacy.py lines 4922-5118. Loaded by app.legacy.
@app.route("/exports")
@login_required
@permission_required("export")
def export_center():
    universities = distinct_values("university_name", "university")
    uni_options = "".join([f"<option value='{safe(x)}'>{safe(x)}</option>" for x in universities])
    content = f"""
    <div class="hero"><h1>مركز التصدير الاحترافي</h1><p>اختر ما تريد تصديره بدقة بدل تصدير كل المستفيدين مرة واحدة.</p></div>
    <div class="grid-3">
      <a class="menu-card" href="{url_for('export_csv')}?user_type=tawjihi">
        <div class="menu-icon"><i class="fa-solid fa-user-graduate"></i></div><h3>تصدير التوجيهي</h3><p>كل طلاب التوجيهي فقط.</p>
      </a>
      <a class="menu-card" href="{url_for('export_csv')}?user_type=freelancer">
        <div class="menu-icon"><i class="fa-solid fa-laptop-code"></i></div><h3>تصدير الفري لانسر</h3><p>كل الفري لانسر فقط.</p>
      </a>
      <a class="menu-card" href="{url_for('export_csv')}?user_type=university">
        <div class="menu-icon"><i class="fa-solid fa-building-columns"></i></div><h3>تصدير الجامعات</h3><p>كل الطلاب الجامعيين فقط.</p>
      </a>
    </div>
    <div class="card" style="margin-top:16px">
      <h3 style="margin-top:0">تصدير مخصص حسب الجامعة</h3>
      <form method="GET" action="{url_for('export_csv')}">
        <div class="row">
          <div>
            <label>الجامعة</label>
            <select name="university_name" required>
              <option value="">اختر الجامعة</option>{uni_options}
            </select>
          </div>
          <div>
            <label>النوع</label>
            <input value="جامعة" disabled>
            <input type="hidden" name="user_type" value="university">
          </div>
        </div>
        <div class="actions" style="margin-top:4px">
          <button class="btn btn-primary" type="submit"><i class="fa-solid fa-file-excel"></i> تصدير الجامعة المحددة</button>
        </div>
      </form>
    </div>
    <div class="card" style="margin-top:16px">
      <h3 style="margin-top:0">تصدير ذكي حسب الفلاتر الحالية</h3>
      <p class="small">من صفحة المستفيدين، أي بحث أو فلترة تطبقها ستنتقل تلقائيًا إلى ملف Excel عند الضغط على زر التصدير.</p>
      <div class="actions">
        <a class="btn btn-secondary" href="{url_for('beneficiaries_page')}"><i class="fa-solid fa-filter"></i> افتح صفحة المستفيدين وحدد الفلاتر</a>
      </div>
    </div>
    """
    return render_page("مركز التصدير", content)
