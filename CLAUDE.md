# HobeHub — قواعد ثابتة لـ Claude

> **هذا الملف يجب أن يُقرأ في بداية أي جلسة عمل على HobeHub.**
> يجمع القرارات المعمارية والتصميمية التي اتُّخذت ولا يجوز التراجع عنها.

---

## 0. الموجَّهات المعمارية الأساسية (Architectural Directives)

**هذا المشروع يجب أن يبقى VPS-ready و future-proof في كل قرار يُتَّخذ.**

### النشر الحالي
- Flask app على **Render**
- تكامل خارجي مع **RADIUS API (app_ad2)**
- **SQLite** للتطوير المحلي، **PostgreSQL** للإنتاج
- العمليات حاليًا **read-heavy**

### البنية المستقبلية المستهدفة
```
Users → Flask → PostgreSQL → WireGuard VPN → MikroTik API
```

### 14 قاعدة معمارية لا يجوز كسرها

1. **الخدمات معيارية وقابلة للاستبدال** — كل service يُكتب كـ ABC + implementations (مثل `RadiusClient`).
2. **لا تفترض Render** — تجنّب أي API/path/feature خاص بـ Render.
3. **لا تثبت IPs أو URLs لـ MikroTik** — كل عناوين MikroTik تأتي من env vars.
4. **التكاملات مدفوعة بـ env/config** — لا hardcoding لأي إعداد قابل للتغيير.
5. **MikroTik معزول في services/** — لمّا نضيفه، يكون `app/services/mikrotik_client/` بنفس نمط `radius_client/`.
6. **استعد لـ PostgreSQL migration** — كل SQL يُكتب ليعمل على الاثنين. الـ schemas مكرّرة بـ `16_sqlite_*` و `17_postgres_*`.
7. **استعد للـ background workers + Redis** — لا تكتب logic ثقيل في view handlers. استخدم نمط "pending action" + queue.
8. **افصل API layer عن cache layer** — `RadiusClient` للـ API، `radius_dashboard.py` للـ cache فقط.
9. **القوالب لا تحتوي business logic** — كل الـ logic في view function أو service، القالب يعرض فقط.
10. **مصمم لـ 3000 مشترك + 200 متصل متزامن** — كل جدول له pagination، كل query مُفهرس، لا N+1.
11. **اترك المجال لـ MikroTik direct control** — `RadiusClient` interface عام بحيث يمكن استبداله بـ `MikrotikClient` بدون تغيير الـ views.
12. **Service-oriented + async-safe حيث ممكن** — تجنّب shared mutable state. الـ helpers يجب أن تكون idempotent.
13. **هيكل مجلدات production-grade** — `app/services/`, `app/templates/`, `app/static/`. (الـ `legacy_parts/` سيُفكَّك تدريجيًا.)
14. **متوافق مع VPS + WireGuard مستقبلًا** — لا افتراضات حول network topology. الـ MikroTik URL يأتي من env.

### أولوية المرحلة الحالية
1. **استقرار UX والـ flows** ← هذا اللي نشتغل عليه الآن
2. **إكمال systems الإدارة**
3. **إكمال systems المشتركين**
4. **اختبار تكامل RADIUS API**
5. **تجنُّب التعقيد المعماري المُبكِّر** — لا تُضِف Redis/Celery/workers إلا عندما يصبح ضروريًا

### قاعدة الذهب
> "أي قرار يجعل المشروع أصعب نشرًا على VPS، أو يُصعِّب استبدال RADIUS بـ MikroTik لاحقًا، هو قرار خاطئ ويجب إعادة النظر فيه."

---

## 1. معيار موحَّد لكل الجداول (Tables Standard)

**كل جدول في HobeHub يلتزم بنفس الشكل الموحَّد. لا استثناء.**

### المواصفات

1. **منتقي عدد الصفوف لكل صفحة** بخيارات: **10 / 20 / 50 / 100**
2. **أزرار تنقّل**: الأولى ⏪ السابقة ◀ أرقام الصفحات ▶ الأخيرة ⏩
3. **شريط معلومات**: «عرض X – Y من Z»
4. **حفظ اختيار حجم الصفحة في localStorage** بمفتاح فريد لكل جدول
5. **التنقّل بين الصفحات بدون reload** — كل الترقيم client-side

### كيف يُطبَّق

المكوّن الجاهز موجود في:
- `app/static/js/dashboard_table.js`
- `app/static/css/dashboard_table.css`

**محمَّلان تلقائيًا** في `app/templates/admin/_admin_layout.html` (head_extra block) — أي صفحة admin ترث هذا الـ layout تحصل عليهما بدون استيراد إضافي.

لتفعيل الترقيم على أي جدول، أضف data attributes:

```html
<table class="d-table"
       data-paginated="1"
       data-page-size="20"
       data-page-sizes="10,20,50,100"
       data-persist-key="my-unique-key">
```

ملاحظات مهمة:
- صفوف الـ empty-state تأخذ `class="no-paginate"` كي لا تُحتسب
- في الـ route، اجلب كل الصفوف اللازمة دفعة واحدة (سقف معقول 500-1000) بدلًا من server-side pagination، لأن الـ JS هو من يقسّمها
- في الصفحات التي ترث `head_extra`، استدعِ `{{ super() }}` أول الـ block حتى يُحمَّل CSS/JS الترقيم

### أمثلة طُبِّقت فعلًا (للمرجع)

- `app/templates/admin/audit/list.html` (key: `audit-log`)
- `app/templates/admin/internet_requests/list.html` (key: `internet-requests`)
- `app/templates/admin/usage_logs/list.html` (key: `usage-logs`)

---

## 2. الهوية البصرية

- **الأسود**: `#1E1E1E` (`--d-black`)
- **الذهبي**: `#F4BA2A` (`--d-gold`)
- **الأبيض/الخلفية الفاتحة**
- النمط: **Premium Corporate** (لا gradients مبالغة، لا ألوان خارج الهوية)

---

## 3. السايد بار الموحَّد

- كل صفحات الإدارة ترث `app/templates/admin/_admin_layout.html`
- السايد بار **يبدأ مطويًا** في كل تحميل صفحة (لا حفظ في localStorage لحالته)
- الـ active state يُحسب من `request.path` تلقائيًا

---

## 4. RADIUS API — قواعد الأمان

- **الـ API mode**: `manual` (لا اتصال) أو `live` — يُتحكَّم به عبر `RADIUS_MODE` env var
- **القراءة فقط مفعّلة** عند `RADIUS_API_READY=1`
- **الكتابة معطّلة** حتى يُضبط `RADIUS_API_WRITES_ENABLED=1` بعد اختبار شامل
- **أي ميزة API لم تُختبر** يجب أن تظهر بوسم **«قيد التطوير»** في الواجهة
- Base URL ينتهي بـ `/app_ad2` (وليس `/app_ad` — التوثيق الأصلي فيه خطأ)

---

## 5. نمط override للـ routes القديمة

عند إعادة تصميم صفحة قديمة:
1. أنشئ template جديد تحت `app/templates/admin/<section>/list.html` يرث `admin/_admin_layout.html`
2. أنشئ ملف `app/legacy_parts/48X_<name>_v2.py` يحتوي على view function جديدة
3. احفظ الـ legacy view كـ fallback: `_legacy_X = app.view_functions.get("X_page")`
4. أنشئ router decorator يخدم القديم عبر `?legacy=1` والجديد افتراضيًا
5. استبدل: `app.view_functions["X_page"] = new_router`
6. أضف اسم الملف إلى قائمة `_LEGACY_PARTS` في `app/legacy.py` قبل `49_main_entrypoint.py`

---

## 6. رؤية الموقع — 3 طبقات

- **الإدارة (Admin)** — `/dashboard`, `/admin/*`
- **مشترك يوزر (Username)** — `/user/account`
- **مشترك بطاقات (Cards)** — `/user/cards`

قواعد الوصول:
- **التوجيهي**: بطاقات فقط
- **الجامعي / العمل الحر**: بطاقات أو يوزر

---

## 7. نصيحة عملية: التعامل مع الـ file flushing

أحيانًا الـ Edit/Write tools تظهر نجاحًا لكن الملف يُحفظ مقطوعًا على القرص (خصوصًا الملفات الكبيرة بمحتوى عربي). الحل:
- بعد كل Edit/Write كبير، تحقق عبر bash: `wc -l <file>` و `tail -5 <file>`
- إن ظهر الملف ناقصًا، أعد كتابته كاملًا عبر heredoc:
  ```bash
  cat > /path/to/file <<'EOF'
  ... content ...
  EOF
  ```
- شغّل `python -m py_compile <file>` للـ Python و فحص `block/endblock` balance للـ Jinja
