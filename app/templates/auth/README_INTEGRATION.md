# دليل دمج قوالب صفحات Auth الجديدة

## الملفات المُسلَّمة

```
app/static/css/auth.css                ← التنسيقات الكاملة (Premium Corporate)
app/templates/auth/
  ├── _layout.html                     ← قالب الأب المشترك (topbar/flashes/footer)
  ├── portal_entry.html                ← /portal — صفحة الإقلاع
  ├── admin_login.html                 ← /login — دخول الإدارة
  ├── user_login.html                  ← /user/login — دخول المشترك
  ├── user_activate.html               ← /user/activate — تفعيل الحساب
  └── user_register.html               ← /user/register — تسجيل اشتراك جديد
```

## ملاحظات تصميمية

- **الألوان محفوظة كما هي** من `base.css`: navy `#123b6d`، sky `#35a7e8`، gold `#f7c948`.
- **خط Almarai** يُستخدم محليًا من `app/static/fonts/`.
- **RTL** مضبوط على عنصر `<html>` و `body`.
- **متجاوب بالكامل** — استخدمت breakpoints ‏1024 / 860 / 520 px لتغطية الشاشات الكبيرة، اللوحي، والموبايل.
- **CSRF** يُدخَل عبر `{{ csrf_token_input() | safe }}` كما هو معتمد في المشروع.
- **Flash messages** تُعرض تلقائيًا في `_layout.html` بالأسلوب الجديد.

## كيفية الدمج في routes الحالية

الـ routes الحالية في `app/legacy_parts/44_redesigned_portal_auth_*.py` تُولّد HTML من سلاسل
Python ثم تستخدم `render_template_string`. يكفي استبدال جسم الدالة بـ `render_template`.

### مثال — `portal_entry`

ضمن `44_redesigned_portal_auth_01.py` استبدل:

```python
def _redesigned_portal_entry():
    content = """..."""
    return render_user_page("واجهة البداية", content)
```

بـ:

```python
from flask import render_template

def _redesigned_portal_entry():
    return render_template("auth/portal_entry.html")
```

### مثال — `login` (الإدارة)

```python
def _redesigned_admin_login():
    if session.get("account_id"):
        return redirect(url_for("dashboard"))
    if session.get("portal_type") == "beneficiary" and session.get("beneficiary_id"):
        return redirect(url_for("user_dashboard"))
    if request.method == "POST":
        # ... كل منطق المصادقة الحالي يبقى كما هو ...
        pass
    return render_template("auth/admin_login.html")
```

نفس النمط للمسارات الثلاثة الأخرى:
- `user_login` → `render_template("auth/user_login.html")`
- `user_activate` → `render_template("auth/user_activate.html")`
- `user_register` → `render_template("auth/user_register.html")`

## تحقق سريع بعد الدمج

```bash
# تأكد أن الـ routes تعمل بدون أخطاء
python -m pytest tests/test_smoke.py -k "test_core_public_pages_render_clean_arabic" -v

# تأكد أن CSRF tokens تُحقن في النماذج
curl -s http://localhost:5000/portal | grep -o '_csrf_token'
```

## التوسع المستقبلي للموبايل

- التصميم بالفعل متجاوب — يعمل على أي شاشة من 320px فأكثر.
- لـ PWA: أضف `manifest.json` + service worker.
- لتطبيق native: يمكن استخدام نفس الـ endpoints مع JSON responses عبر إعادة كتابة بسيطة في `app/api/`.
