# Continued split from 30_template_overrides.py lines 96-229. Loaded by app.legacy.

BASE_TEMPLATE = BASE_TEMPLATE.replace(
"""    <div class="nav">
      <a href="{{ url_for('dashboard') }}"><i class="fa-solid fa-gauge"></i><span class="nav-label">لوحة التحكم</span></a>
      <a href="{{ url_for('beneficiaries_page') }}"><i class="fa-solid fa-users"></i><span class="nav-label">المستفيدون</span></a>
      <a href="{{ url_for('usage_logs_page') }}"><i class="fa-solid fa-ticket"></i><span class="nav-label">سجل البطاقات</span></a>
      {% if has_permission('view_archive') %}
      <a href="{{ url_for('usage_archive_page') }}"><i class="fa-solid fa-box-archive"></i><span class="nav-label">أرشيف البطاقات</span></a>
      {% endif %}
      <a href="{{ url_for('power_timer_page') }}"><i class="fa-solid fa-bolt"></i><span class="nav-label">مؤقت الكهرباء</span></a>
      {% if has_permission('manage_bulk_ops') or has_permission('manage_system_cleanup') %}
      <a href="{{ url_for('admin_control_panel') }}"><i class="fa-solid fa-sliders"></i><span class="nav-label">لوحة التحكم المتقدم</span></a>
      {% endif %}
      {% if has_permission('add') %}
      <details open>
        <summary><i class="fa-solid fa-user-plus"></i><span class="nav-label">إضافة مستفيد</span></summary>
        <div class="submenu">
          <a href="{{ url_for('add_beneficiary_page') }}?user_type=tawjihi"><i class="fa-solid fa-user-graduate"></i><span class="nav-label">طالب توجيهي</span></a>
          <a href="{{ url_for('add_beneficiary_page') }}?user_type=university"><i class="fa-solid fa-building-columns"></i><span class="nav-label">طالب جامعي</span></a>
          <a href="{{ url_for('add_beneficiary_page') }}?user_type=freelancer"><i class="fa-solid fa-laptop-code"></i><span class="nav-label">فري لانسر</span></a>
        </div>
      </details>
      {% endif %}
      {% if has_permission('import') %}
      <a href="{{ url_for('import_page') }}"><i class="fa-solid fa-file-arrow-up"></i><span class="nav-label">استيراد CSV</span></a>
      {% endif %}
      {% if has_permission('export') %}
      <a href="{{ url_for('export_center') }}"><i class="fa-solid fa-file-arrow-down"></i><span class="nav-label">مركز التصدير</span></a>
      {% endif %}
      {% if has_permission('backup') %}
      <a href="{{ url_for('backup_sql') }}"><i class="fa-solid fa-database"></i><span class="nav-label">Backup SQL</span></a>
      {% endif %}
      <div class="section">الحساب</div>
      <a href="{{ url_for('profile_page') }}"><i class="fa-solid fa-id-badge"></i><span class="nav-label">صفحتي الشخصية</span></a>
      {% if has_permission('manage_accounts') %}
      <a href="{{ url_for('accounts_page') }}"><i class="fa-solid fa-user-shield"></i><span class="nav-label">إدارة المستخدمين</span></a>
      {% endif %}
      {% if has_permission('view_audit_log') %}
      <a href="{{ url_for('audit_log_page') }}"><i class="fa-solid fa-clock-rotate-left"></i><span class="nav-label">سجل العمليات</span></a>
      {% endif %}
    </div>
""",
"""    <div class="nav">
      {% set path = request.path %}
      <div class="nav-group">
        <div class="nav-group-label"><i class="fa-solid fa-gauge-high"></i><span class="nav-label">لوحة التحكم</span></div>
        <a href="{{ url_for('admin_dashboard_alias') }}" class="{% if path == '/admin' or path == '/admin/dashboard' or path == '/dashboard' %}active{% endif %}"><i class="fa-solid fa-house"></i><span class="nav-label">الرئيسية</span></a>
        <a href="{{ url_for('admin_dashboard_alias') }}#kpi-overview" class="{% if path == '/admin' or path == '/admin/dashboard' or path == '/dashboard' %}active{% endif %}"><i class="fa-solid fa-chart-line"></i><span class="nav-label">الإحصائيات السريعة</span></a>
      </div>
      <div class="nav-group">
        <div class="nav-group-label"><i class="fa-solid fa-users"></i><span class="nav-label">المستفيدون</span></div>
        <a href="{{ url_for('admin_beneficiaries_alias') }}" class="{% if path == '/admin/beneficiaries' or path == '/beneficiaries' %}active{% endif %}"><i class="fa-solid fa-users-viewfinder"></i><span class="nav-label">جميع المستفيدين</span></a>
        {% if has_permission('manage_accounts') %}
        <a href="{{ url_for('admin_portal_accounts_page') }}" class="{% if path == '/admin/portal-accounts' %}active{% endif %}"><i class="fa-solid fa-id-card-clip"></i><span class="nav-label">حسابات البوابة</span></a>
        {% endif %}
        <details {% if path == '/admin/beneficiaries' or path == '/beneficiaries' %}open{% endif %}>
          <summary class="{% if path == '/admin/beneficiaries' or path == '/beneficiaries' %}active{% endif %}"><i class="fa-solid fa-network-wired"></i><span class="nav-label">أنواع الوصول</span></summary>
          <div class="submenu">
            <a href="{{ url_for('admin_beneficiaries_alias') }}?internet_method=username"><i class="fa-solid fa-user"></i><span class="nav-label">يوزر إنترنت</span></a>
            <a href="{{ url_for('admin_beneficiaries_alias') }}?internet_method=cards"><i class="fa-solid fa-ticket"></i><span class="nav-label">بطاقات استخدام</span></a>
          </div>
        </details>
        <a href="{{ url_for('admin_dashboard_alias') }}#recent-activity" class="{% if path == '/admin' or path == '/admin/dashboard' or path == '/dashboard' %}active{% endif %}"><i class="fa-solid fa-wave-square"></i><span class="nav-label">النشاط الأخير</span></a>
      </div>
      <div class="nav-group">
        <div class="nav-group-label"><i class="fa-solid fa-globe"></i><span class="nav-label">خدمات الإنترنت</span></div>
        <a href="{{ url_for('admin_internet_requests_page') }}" class="{% if path == '/admin/internet-requests' %}active{% endif %}"><i class="fa-solid fa-list-check"></i><span class="nav-label">طلبات الإنترنت</span></a>
        {% if has_permission('submit_internet_requests') %}
        <a href="{{ url_for('internet_request_page') }}" class="{% if path == '/internet/request' %}active{% endif %}"><i class="fa-solid fa-plus"></i><span class="nav-label">إنشاء طلب يدوي</span></a>
        {% endif %}
        <a href="{{ url_for('admin_internet_requests_page') }}?status=pending" class="{% if path == '/admin/internet-requests' and request.args.get('status') == 'pending' %}active{% endif %}"><i class="fa-regular fa-hourglass-half"></i><span class="nav-label">الطلبات المعلقة</span></a>
        <a href="{{ url_for('admin_internet_requests_page') }}?status=executed" class="{% if path == '/admin/internet-requests' and request.args.get('status') == 'executed' %}active{% endif %}"><i class="fa-solid fa-circle-check"></i><span class="nav-label">الطلبات المنفذة</span></a>
      </div>
      <div class="nav-group">
        <div class="nav-group-label"><i class="fa-solid fa-satellite-dish"></i><span class="nav-label">RADIUS والاتصال</span></div>
        <a href="{{ url_for('radius_online_users_page') }}" class="{% if path == '/admin/radius/users-online' %}active{% endif %}"><i class="fa-solid fa-wifi"></i><span class="nav-label">المستخدمون المتصلون</span></a>
        <a href="{{ url_for('radius_user_lookup_page') }}" class="{% if path == '/admin/radius/user-lookup' %}active{% endif %}"><i class="fa-solid fa-magnifying-glass"></i><span class="nav-label">البحث عن مستخدم</span></a>
        <a href="{{ url_for('radius_user_lookup_page') }}" class="{% if path == '/admin/radius/user-lookup' %}active{% endif %}"><i class="fa-solid fa-chart-column"></i><span class="nav-label">الجلسات والاستخدام</span></a>
        {% if has_permission('disconnect_radius_user') %}
        <a href="{{ url_for('radius_online_users_page') }}" class="{% if path == '/admin/radius/users-online' %}active{% endif %}"><i class="fa-solid fa-plug-circle-xmark"></i><span class="nav-label">فصل مستخدم</span></a>
        {% endif %}
        <a href="{{ url_for('radius_settings_page') }}" class="{% if path == '/admin/radius/settings' %}active{% endif %}"><i class="fa-solid fa-plug-circle-bolt"></i><span class="nav-label">إعدادات الربط</span></a>
      </div>
      <div class="nav-group">
        <div class="nav-group-label"><i class="fa-solid fa-ticket"></i><span class="nav-label">البطاقات</span></div>
        <a href="{{ url_for('usage_logs_page') }}" class="{% if path == '/usage-logs' or path == '/admin/usage-logs' %}active{% endif %}"><i class="fa-solid fa-ticket-simple"></i><span class="nav-label">بطاقات الاستخدام</span></a>
        {% if has_permission('view_archive') %}
        <a href="{{ url_for('usage_archive_page') }}" class="{% if path == '/archive' or path == '/admin/archive' %}active{% endif %}"><i class="fa-solid fa-box-archive"></i><span class="nav-label">البطاقات المصدرة</span></a>
        {% endif %}
        <a href="{{ url_for('admin_dashboard_alias') }}#card-insights" class="{% if path == '/admin' or path == '/admin/dashboard' or path == '/dashboard' %}active{% endif %}"><i class="fa-solid fa-chart-pie"></i><span class="nav-label">إحصائيات البطاقات</span></a>
      </div>
      <div class="nav-group">
        <div class="nav-group-label"><i class="fa-solid fa-folder-tree"></i><span class="nav-label">السجلات والإدارة</span></div>
        {% if has_permission('view_audit_log') %}
        <a href="{{ url_for('audit_log_page') }}" class="{% if path == '/audit-log' or path == '/admin/audit-log' %}active{% endif %}"><i class="fa-solid fa-clock-rotate-left"></i><span class="nav-label">سجل العمليات</span></a>
        {% endif %}
        {% if has_permission('view_archive') %}
        <a href="{{ url_for('usage_archive_page') }}" class="{% if path == '/archive' or path == '/admin/archive' %}active{% endif %}"><i class="fa-solid fa-box-open"></i><span class="nav-label">الأرشيف</span></a>
        {% endif %}
        {% if has_permission('import') %}
        <a href="{{ url_for('import_page') }}" class="{% if path == '/import' or path == '/admin/import' %}active{% endif %}"><i class="fa-solid fa-file-arrow-up"></i><span class="nav-label">الاستيراد</span></a>
        {% endif %}
        {% if has_permission('export') %}
        <a href="{{ url_for('export_center') }}" class="{% if path == '/exports' or path == '/admin/exports' %}active{% endif %}"><i class="fa-solid fa-file-arrow-down"></i><span class="nav-label">التصدير</span></a>
        {% endif %}
        {% if has_permission('manage_bulk_ops') or has_permission('manage_system_cleanup') %}
        <a href="{{ url_for('admin_control_panel') }}" class="{% if path == '/admin/system-cleanup' or path == '/admin-control-panel' %}active{% endif %}"><i class="fa-solid fa-sliders"></i><span class="nav-label">تنظيف النظام</span></a>
        {% endif %}
      </div>
      <div class="nav-group">
        <div class="nav-group-label"><i class="fa-solid fa-gear"></i><span class="nav-label">الإعدادات</span></div>
        <a href="{{ url_for('profile_page') }}" class="{% if path == '/profile' or path == '/admin/profile' %}active{% endif %}"><i class="fa-solid fa-id-badge"></i><span class="nav-label">الحساب الشخصي</span></a>
        {% if has_permission('manage_accounts') %}
        <a href="{{ url_for('accounts_page') }}" class="{% if path == '/accounts' or path == '/admin/accounts' %}active{% endif %}"><i class="fa-solid fa-user-shield"></i><span class="nav-label">الحسابات والصلاحيات</span></a>
        {% endif %}
        <a href="{{ url_for('power_timer_page') }}" class="{% if path == '/timer' or path == '/admin/timer' %}active{% endif %}"><i class="fa-solid fa-bolt"></i><span class="nav-label">مؤقت الكهرباء</span></a>
        <a href="{{ url_for('user_login') }}"><i class="fa-solid fa-arrow-up-right-from-square"></i><span class="nav-label">بوابة المستفيد</span></a>
      </div>
    </div>
""",
)

BASE_TEMPLATE = BASE_TEMPLATE.replace(
    """<div class="topbar-left"><button class="sidebar-toggle" type="button" onclick="return toggleSidebar()" title="إظهار/إخفاء القائمة الجانبية"><i class="fa-solid fa-bars"></i></button><strong>{{ title }}</strong></div>""",
    """<div class="topbar-left"><button class="sidebar-toggle" type="button" onclick="return toggleSidebar()" title="إظهار/إخفاء القائمة الجانبية"><i class="fa-solid fa-bars"></i></button><div class="topbar-title"><strong>{{ title }}</strong><small>واجهة الإدارة والتشغيل</small></div></div>""",
)

BASE_TEMPLATE = BASE_TEMPLATE.replace(
    """<span class="badge">{{ session.get('username','') }}</span>""",
    """<span class="badge badge-blue">الإدارة</span><span class="badge">{{ session.get('username','') }}</span>""",
    1,
)

for _old_admin_link, _new_admin_link in {
    "{{ url_for('dashboard') }}": "/admin/dashboard",
    "{{ url_for('beneficiaries_page') }}": "/admin/beneficiaries",
    "{{ url_for('add_beneficiary_page') }}": "/admin/beneficiaries/add",
    "{{ url_for('usage_logs_page') }}": "/admin/usage-logs",
    "{{ url_for('usage_archive_page') }}": "/admin/usage-archive",
    "{{ url_for('power_timer_page') }}": "/admin/timer",
    "{{ url_for('import_page') }}": "/admin/import",
    "{{ url_for('export_center') }}": "/admin/exports",
    "{{ url_for('backup_sql') }}": "/admin/backup-sql",
    "{{ url_for('profile_page') }}": "/admin/profile",
    "{{ url_for('accounts_page') }}": "/admin/accounts",
    "{{ url_for('audit_log_page') }}": "/admin/audit-log",
}.items():
    BASE_TEMPLATE = BASE_TEMPLATE.replace(_old_admin_link, _new_admin_link)

USER_BASE_TEMPLATE = _legacy_template_text('30_template_overrides.USER_BASE_TEMPLATE.html')
