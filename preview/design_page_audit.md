# HobeHub Page Design Audit

تاريخ الفحص: 2026-05-16  
قاعدة المعاينة: http://127.0.0.1:5000

## الخلاصة

| التصنيف | العدد | القرار |
|---|---:|---|
| جديد | 35 | يبقى |
| مختلط | 23 | يوحد لاحقا على قوالب Jinja الجديدة |
| قديم | 7 | يستبدل أو ينقل لتصميم جديد |
| قديم مكرر Redirect | 41 | يحذف بعد التأكد من عدم استعماله داخليا |

## معنى التصنيفات

- جديد: يستخدم التصميم الحديث أو مسار واضح ضمن `/admin`, `/user`, `/card`.
- مختلط: المسار جديد غالبا، لكن الصفحة ما زالت مبنية من legacy/render string أو shell قديم.
- قديم: صفحة عاملة لكن شكلها/تنفيذها قديم أو ليست صفحة HTML معاينة كاملة.
- قديم مكرر Redirect: الرابط القديم لا يعرض صفحة مستقلة، بل يحول إلى بديل جديد.

## صفحات جديدة تبقى

| الصفحة | رابط المعاينة |
|---|---|
| بوابة البداية | [فتح](/portal) |
| دخول الإدارة | [فتح](/login) |
| دخول اليوزر | [فتح](/user/login) |
| دخول البطاقات | [فتح](/card/login) |
| تسجيل مشترك | [فتح](/user/register) |
| تفعيل مشترك | [فتح](/user/activate) |
| ملف المشترك | [فتح](/user/profile) |
| داشبورد اليوزر | [فتح](/user/account) |
| تغيير كلمة مرور اليوزر | [فتح](/user/account/change-password) |
| فتح موقع للّيوزر | [فتح](/user/account/unblock-site) |
| رفع سرعة اليوزر | [فتح](/user/account/speed-upgrade) |
| طلبات اليوزر | [فتح](/user/account/requests) |
| طلب إنترنت اليوزر | [فتح](/user/internet/request) |
| داشبورد البطاقات | [فتح](/card) |
| سجل بطاقات المشترك | [فتح](/card/history) |
| طلبات البطاقات المعلقة | [فتح](/card/pending) |
| Admin API Test | [فتح](/admin/api/test) |
| مستفيدون جديد v2 | [فتح](/admin/beneficiaries-new) |
| إدارة البطاقات | [فتح](/admin/cards) |
| Overview البطاقات | [فتح](/admin/cards/overview) |
| تدقيق البطاقات | [فتح](/admin/cards/audit) |
| فئات البطاقات | [فتح](/admin/cards/categories) |
| مزامنة الفئات مع profiles | [فتح](/admin/cards/categories/sync-profiles) |
| تسليمات البطاقات | [فتح](/admin/cards/deliveries) |
| بطاقات معلقة | [فتح](/admin/cards/pending) |
| سياسات البطاقات | [فتح](/admin/cards/policies) |
| صفحة Admin Home | [فتح](/admin/home) |
| طلبات الإنترنت الإدارية | [فتح](/admin/internet-requests) |
| Radius Online | [فتح](/admin/radius/online) |
| Radius Settings | [فتح](/admin/radius/settings) |
| إدارة حسابات اليوزر | [فتح](/admin/users-account) |
| إدارة حسابات اليوزر - Overview | [فتح](/admin/users-account/overview) |
| قائمة حسابات اليوزر | [فتح](/admin/users-account/list) |
| طلبات حسابات اليوزر | [فتح](/admin/users-account/requests) |

## صفحات مختلطة تحتاج توحيد

هذه لا نحذفها الآن لأنها صفحات فعلية، لكن ننقل محتواها لاحقا إلى templates جديدة ونزيل render string/legacy.

| الصفحة | رابط المعاينة | الملاحظة |
|---|---|---|
| لوحة التحكم | [فتح](/admin/dashboard) | مسار جديد، محتوى/قالب legacy |
| الحسابات والصلاحيات | [فتح](/admin/accounts) | مسار جديد، محتوى legacy |
| إضافة حساب | [فتح](/admin/accounts/add) | مسار جديد، محتوى legacy |
| تعديل حساب مثال 1 | [فتح](/admin/accounts/edit/1) | مسار جديد، محتوى legacy |
| سجل العمليات | [فتح](/admin/audit-log) | مسار جديد، محتوى legacy |
| المستفيدون | [فتح](/admin/beneficiaries) | يوجد بديل أحدث: [فتح](/admin/beneficiaries-new) |
| إضافة مستفيد | [فتح](/admin/beneficiaries/add) | مسار جديد، محتوى legacy |
| تعديل مستفيد مثال 1 | [فتح](/admin/beneficiaries/edit/1) | مسار جديد، محتوى legacy |
| استيراد بطاقات | [فتح](/admin/cards/import) | مسار جديد، محتوى legacy |
| جرد البطاقات | [فتح](/admin/cards/inventory) | مسار جديد، محتوى legacy |
| إعدادات البطاقات | [فتح](/admin/cards/settings) | مسار جديد، محتوى legacy |
| مركز التصدير | [فتح](/admin/exports) | مسار جديد، محتوى legacy |
| الاستيراد | [فتح](/admin/import) | مسار جديد، محتوى legacy |
| تفاصيل طلب إنترنت مثال 1 | [فتح](/admin/internet-requests/1) | مسار جديد، محتوى legacy |
| حسابات البوابة | [فتح](/admin/portal-accounts) | مسار جديد، محتوى legacy |
| الملف الشخصي للإدارة | [فتح](/admin/profile) | مسار جديد، محتوى legacy |
| اختبار RADIUS API | [فتح](/admin/radius/app-test) | مسار جديد، محتوى legacy |
| بحث مستخدم RADIUS | [فتح](/admin/radius/user-lookup) | مسار جديد، محتوى legacy |
| المتصلون الآن RADIUS | [فتح](/admin/radius/users-online) | مسار جديد، محتوى legacy |
| تنظيف النظام | [فتح](/admin/system-cleanup) | مسار جديد، محتوى legacy |
| مؤقت الكهرباء | [فتح](/admin/timer) | مسار جديد، محتوى legacy |
| أرشيف الاستخدام | [فتح](/admin/usage-archive) | مسار جديد، محتوى legacy |
| سجل الاستخدام | [فتح](/admin/usage-logs) | مسار جديد، محتوى legacy |

## صفحات قديمة أو ليست واجهة حديثة

| الصفحة | رابط المعاينة | البديل/القرار |
|---|---|---|
| SQL Backup | [فتح](/admin/backup-sql) | ليست واجهة حديثة؛ تعامل كتنزيل/أداة لا كصفحة تصميم |
| Export CSV | [فتح](/admin/exports/csv) | تنزيل/تصدير؛ لا تحتاج صفحة تصميم |
| Export Template | [فتح](/admin/exports/template) | تنزيل قالب؛ لا تحتاج صفحة تصميم |
| Export Archive | [فتح](/admin/usage-archive/export) | تنزيل/تصدير؛ لا تحتاج صفحة تصميم |
| User Internet Overview | [فتح](/user/internet) | قديم؛ يدمج مع [طلبات اليوزر](/user/account/requests) أو [طلب إنترنت](/user/internet/request) |
| User Internet Access | [فتح](/user/internet/my-access) | قديم؛ يدمج مع [داشبورد اليوزر](/user/account) |
| User Internet Requests | [فتح](/user/internet/my-requests) | قديم؛ يدمج مع [طلبات اليوزر](/user/account/requests) |

## روابط قديمة مكررة ولها بديل جديد

هذه مرشحة للحذف بعد فحص أن السايدبار والقوالب والكود الداخلي لم تعد تستدعيها. حاليا كلها تعمل redirect.

| الرابط القديم | البديل الجديد |
|---|---|
| [/](/) | [/admin/dashboard](/admin/dashboard) |
| [/dashboard](/dashboard) | [/admin/dashboard](/admin/dashboard) |
| [/admin](/admin) | [/admin/dashboard](/admin/dashboard) |
| [/admin-control](/admin-control) | [/admin/system-cleanup](/admin/system-cleanup) |
| [/accounts](/accounts) | [/admin/accounts](/admin/accounts) |
| [/accounts/add](/accounts/add) | [/admin/accounts/add](/admin/accounts/add) |
| [/accounts/edit/1](/accounts/edit/1) | [/admin/accounts/edit/1](/admin/accounts/edit/1) |
| [/audit-log](/audit-log) | [/admin/audit-log](/admin/audit-log) |
| [/backup_sql](/backup_sql) | [/admin/backup-sql](/admin/backup-sql) |
| [/beneficiaries](/beneficiaries) | [/admin/beneficiaries](/admin/beneficiaries) |
| [/beneficiaries/add](/beneficiaries/add) | [/admin/beneficiaries/add](/admin/beneficiaries/add) |
| [/beneficiaries/edit/1](/beneficiaries/edit/1) | [/admin/beneficiaries/edit/1](/admin/beneficiaries/edit/1) |
| [/download_template](/download_template) | [/admin/exports/template](/admin/exports/template) |
| [/export_csv](/export_csv) | [/admin/exports/csv](/admin/exports/csv) |
| [/exports](/exports) | [/admin/exports](/admin/exports) |
| [/import](/import) | [/admin/import](/admin/import) |
| [/profile](/profile) | [/admin/profile](/admin/profile) |
| [/timer](/timer) | [/admin/timer](/admin/timer) |
| [/usage-logs](/usage-logs) | [/admin/usage-logs](/admin/usage-logs) |
| [/usage-archive](/usage-archive) | [/admin/usage-archive](/admin/usage-archive) |
| [/usage-archive/export](/usage-archive/export) | [/admin/usage-archive/export](/admin/usage-archive/export) |
| [/admin/archive](/admin/archive) | [/admin/usage-archive](/admin/usage-archive) |
| [/cards](/cards) | [/card](/card) |
| [/cards/history](/cards/history) | [/card/history](/card/history) |
| [/cards/pending](/cards/pending) | [/card/pending](/card/pending) |
| [/user/cards](/user/cards) | [/card](/card) |
| [/user/cards/history](/user/cards/history) | [/card/history](/card/history) |
| [/user/cards/pending](/user/cards/pending) | [/card/pending](/card/pending) |
| [/user/dashboard](/user/dashboard) | [/user/account](/user/account) |
| [/user/set-password](/user/set-password) | [/user/activate](/user/activate) |
| [/users/account](/users/account) | [/user/account](/user/account) |
| [/users/change-password](/users/change-password) | [/user/account/change-password](/user/account/change-password) |
| [/users/requests](/users/requests) | [/user/account/requests](/user/account/requests) |
| [/users/speed-upgrade](/users/speed-upgrade) | [/user/account/speed-upgrade](/user/account/speed-upgrade) |
| [/users/unblock-site](/users/unblock-site) | [/user/account/unblock-site](/user/account/unblock-site) |
| [/internet/request](/internet/request) | [/user/internet/request](/user/internet/request) |
| [/internet/my-requests](/internet/my-requests) | [/user/internet/my-requests](/user/internet/my-requests) |
| [/internet/my-access](/internet/my-access) | [/user/internet/my-access](/user/internet/my-access) |
| [/users/internet/request](/users/internet/request) | [/user/internet/request](/user/internet/request) |
| [/users/internet/my-requests](/users/internet/my-requests) | [/user/internet/my-requests](/user/internet/my-requests) |
| [/users/internet/my-access](/users/internet/my-access) | [/user/internet/my-access](/user/internet/my-access) |

## أولوية العمل المقترحة

1. احذف/عطّل روابط redirect القديمة بعد التأكد من عدم وجود استعمال داخلي لها.
2. وحد صفحات `/user/internet/*` القديمة داخل داشبورد اليوزر الجديد.
3. اجعل `/admin/beneficiaries-new` هو صفحة المستفيدين الأساسية بدل `/admin/beneficiaries`.
4. انقل صفحات الإدارة المختلطة إلى templates جديدة حسب التخصص.
5. تعامل مع صفحات التنزيل مثل backup/export كأزرار/أدوات داخل صفحات حديثة، وليس صفحات مستقلة.
