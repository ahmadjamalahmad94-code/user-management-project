# سجل التغييرات — HobeHub

كل التحديثات الأخيرة موثّقة هنا بترتيب تنازلي (الأحدث أعلى).

---

## النسخة الحالية — التصميم الموحّد + AJAX live search + Kill-switch + إصلاح PostgreSQL

### إصلاح حرج: PostgreSQL boolean = integer
PostgreSQL صارم في الأنواع: `is_active = 1` لا يعمل لأن العمود `BOOLEAN`. SQLite كان يقبل ذلك.
الحل: استبدال كل `=1` / `=0` في SQL strings بـ `=TRUE` / `=FALSE` (يعمل في الـ dialect الاثنين).

**الملفات المُصلَحة:**
- `services/quota_engine.py` — كل استعلامات `is_active=1` → `is_active=TRUE`
- `legacy_parts/48q_admin_cards_inventory_controls.py` — `cc.is_active = 1` → `cc.is_active = TRUE`
- `legacy_parts/45a_admin_cards_v2_routes.py` — INSERT values + toggle endpoints بـ `bool` Python
- `legacy_parts/48ad_cards_policies_ajax.py` — INSERT VALUES `1` → `TRUE`
- `legacy_parts/48af_cards_categories_ajax.py` — INSERT VALUES `1` → `TRUE`
- `legacy_parts/48ah_portal_import.py` — `must_set_password=0` → `FALSE`، VALUES `1,0` → `TRUE,FALSE`
- `legacy_parts/48ai_unified_login.py` — `must_set_password=0` → `FALSE`
- `legacy_parts/48x_portal_accounts_v2.py` — `must_set_password=0` → `FALSE`
- `legacy_parts/48y_phase1_portal_section.py` — `must_set_password=1/0`، `is_active=1` → `TRUE/FALSE`

ملاحظة: ملفات `16_sqlite_*` و `15_sqlite_seed_data.py` بقيت بـ `=1`/`=0` لأنها تعمل على SQLite فقط.

---

### ميزات جديدة كبيرة

#### 1. Control Hub موحّد لجميع صفحات الإدارة
تم إنشاء تصميم رأسي موحّد يجمع كل المعلومات في كرت واحد متناسق:
- شريط KPIs (إحصائيات) بألوان متمايزة + شارات نبض على الأرقام النشطة
- شريط pills (حبوب الفلترة/الأقسام)
- شريط بحث مدمج مع spinner ذهبي

**الصفحات المُحوّلة:**
- `/admin/users-account` — مشتركو حساب الإنترنت
- `/admin/cards/subscribers` — مشتركو البطاقات
- `/admin/beneficiaries` — كل المستفيدين
- `/admin/portal-accounts` — حسابات بوابة المشتركين
- `/admin/internet-requests` — مركز طلبات الإنترنت
- `/admin/usage-logs` — سجل البطاقات (مع أدوات الأرشفة)
- `/admin/cards` — نظرة عامة على البطاقات
- `/admin/cards/inventory` — المخزون
- `/admin/cards/deliveries` — سجل التسليمات
- `/admin/requests` — مركز الطلبات الموحّد
- `/admin/usage-archive` — أرشيف السجل
- `/admin/sms/log` — سجل الرسائل

**الملفات الجديدة:**
- `app/static/css/dashboard_hub.css` — أنماط الـ Hub العامة
- `app/static/js/dashboard_hub_search.js` — helper generic للبحث AJAX

#### 2. AJAX live search في كل الصفحات
البحث المباشر بدون إعادة تحميل (debounce 280ms على الكتابة، فوري على selects):
- spinner ذهبي يدور أثناء البحث، علامة ✓ خضراء عند الانتهاء
- الـ URL يتحدّث عبر `history.replaceState` فتقدر تنسخ الرابط أو F5
- الإحصائيات في الـ Hub تتحدّث مع كل بحث
- pagination تُعاد تهيئتها تلقائياً بعد كل rerender
- زر مسح ✕ يفرّغ كل الحقول دفعة واحدة

#### 3. RADIUS API Kill-switch
ملف جديد `app/services/radius_kill_switch.py` يعطّل كل استدعاءات API بأمان:
- `is_radius_offline()`: يرجع `True` بالافتراضي (معطّل)
- للتفعيل الرسمي لاحقاً: ضبط `RADIUS_API_LIVE=1` في البيئة
- مطبّق في: `radius_subscriber_bridge.py`, `radius_dashboard.py`, `card_status_service.py`, `subscriber_radius_status.py`

#### 4. فصل كلمة مرور RADIUS عن كلمة مرور البوابة
- كلمة مرور البوابة (`beneficiary_portal_accounts.password_plain`): للدخول للموقع فقط
- كلمة مرور RADIUS (`beneficiary_radius_accounts.plain_password`): للـ API الخارجية
- مستقلّتان، تعديل واحدة لا يؤثر على الأخرى
- استيراد CSV «حسابات إنترنت» يحفظ في جدول RADIUS مباشرة

#### 5. مركز استيراد محدّث
- تبويبان جديدان: «حسابات إنترنت» و«حسابات بطاقات»
- دعم Excel (.xlsx + .xls) إضافة لـ CSV
- JavaScript drag-and-drop + AJAX submit مع spinner

### تحسينات الأداء

#### إصلاح بطء صفحة `/admin/cards/inventory`
كانت تستدعي RADIUS API لكل بطاقة صادرة (حتى 100 استدعاء متسلسل) — صار `include_usage=False` يجلب الجدول instantly.

#### تحسين الـ RADIUS hydration في users-account
- خفّض الجلب التلقائي من 20 إلى 10 صف
- بدّل سيرفر سلسلة → تزامن 3 طلبات
- token system لإلغاء عمليات الجلب القديمة عند تغيير الفلتر
- زر «تحديث حالة RADIUS» يدوي لكامل الصفحة

### إصلاحات صغيرة
- `delete_beneficiary` يدعم AJAX (يرجع JSON عند XHR، redirect عند طلب عادي)
- يحترم الـ referrer فلا يقفز للصفحة الرئيسية بعد الحذف من users-account
- توحيد ارتفاع الـ pills (34px) عبر كل الأنواع
- spinner status في كل البحوث
- تحسين الأيقونات والـ hover effects

### تصميم بصري
- خلفية سوداء متدرجة + توهج ذهبي شبه شفاف في زوايا الـ Hub
- أيقونات بـ gradient + shadow ملوّن (warn / ok / muted / cyan / danger)
- pulse animation حول الأيقونات النشطة فعلياً (>0)
- pills بلون ذهبي عند الـ active
- focus glow ذهبي في الـ inputs

---

## للتفعيل اللاحق

عند جاهزية RADIUS API الرسمية:
```bash
export RADIUS_API_LIVE=1
export RADIUS_API_READY=1
```
ثم إعادة تشغيل التطبيق. كل الاستدعاءات ترجع تعمل بدون أي تغيير في الكود.
