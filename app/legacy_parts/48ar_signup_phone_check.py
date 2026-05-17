# 48ar_signup_phone_check.py
# ─────────────────────────────────────────────────────────────────────
# تسجيل اشتراك جديد بمسار من خطوتين:
#   1) المشترك يدخل رقم جواله → API يفحص إذا الرقم مسجل في أي مكان.
#      - إن وُجد → رسالة "راجع الإدارة للحصول على رمز التفعيل".
#      - إن لم يُوجد → الواجهة تفتح نموذج تسجيل اشتراك كامل.
#   2) المشترك يملأ النموذج → الطلب يُحفظ في beneficiary_signup_requests.
#
# الـ endpoints:
#   GET  /user/register                  → الصفحة الجديدة (overrides legacy /user/register)
#   POST /user/register/check-phone      → AJAX يرجع JSON عن حالة الرقم
#   POST /user/register/submit           → AJAX يحفظ الطلب في DB

from flask import jsonify, render_template, request, redirect, url_for, flash, session


# ─── جدول البحث: أي جدول فيه phone column؟ ──────────────────────
def _find_phone_anywhere(phone: str) -> dict:
    """يفحص إن كان الرقم موجوداً في أي مكان في النظام.

    يرجع dict فيه:
      - found: bool
      - source: 'beneficiaries' | 'signup_requests' | 'portal_username'
      - status: 'active' | 'pending' | 'reset' | ...
      - hint: نص توضيحي يظهر للمشترك
    """
    phone = (phone or "").strip()
    if not phone:
        return {"found": False}

    # تطبيع الرقم: ابقي الأرقام فقط
    digits = "".join(c for c in phone if c.isdigit())
    if not digits:
        return {"found": False}

    # 1) جدول المستفيدين الرئيسي
    ben = query_one(
        "SELECT id, full_name, user_type FROM beneficiaries WHERE phone=%s LIMIT 1",
        [digits],
    )
    if ben:
        return {
            "found": True,
            "source": "beneficiary",
            "status": "registered",
            "hint": "هذا الرقم مسجّل لديكم بالفعل. راجع الإدارة للحصول على رمز التفعيل.",
        }

    # 2) جدول حسابات البوابة (اسم المستخدم عادةً = رقم الجوال)
    portal = query_one(
        "SELECT id, username FROM beneficiary_portal_accounts WHERE username=%s LIMIT 1",
        [digits],
    )
    if portal:
        return {
            "found": True,
            "source": "portal_account",
            "status": "has_account",
            "hint": "هذا الرقم له حساب بوابة بالفعل. راجع الإدارة للحصول على رمز التفعيل.",
        }

    # 3) جدول طلبات الاشتراك المعلّقة
    try:
        existing_req = query_one(
            "SELECT id, status FROM beneficiary_signup_requests WHERE phone=%s ORDER BY id DESC LIMIT 1",
            [digits],
        )
        if existing_req:
            status = (existing_req.get("status") or "").lower()
            if status in {"pending", "review", ""}:
                return {
                    "found": True,
                    "source": "signup_request",
                    "status": "pending",
                    "hint": "لديك طلب اشتراك قيد المراجعة. سيتواصل معك المدير قريباً.",
                }
            elif status in {"approved", "accepted"}:
                return {
                    "found": True,
                    "source": "signup_request",
                    "status": "approved",
                    "hint": "تم اعتماد طلبك. راجع الإدارة للحصول على رمز التفعيل.",
                }
            # rejected/cancelled — نسمح بتسجيل جديد
    except Exception:
        # الجدول قد لا يكون موجود — نتجاهل بهدوء
        pass

    return {"found": False}


# ─── AJAX: POST /user/register/check-phone ─────────────────────
@app.route("/user/register/check-phone", methods=["POST"])
def signup_check_phone():
    phone = (request.form.get("phone") or "").strip()
    if not phone:
        return jsonify({"ok": False, "message": "أدخل رقم الجوال أولاً."}), 400

    # تطبيع: ابقي 10 أرقام تبدأ بـ 0
    digits = "".join(c for c in phone if c.isdigit())
    if len(digits) < 9 or len(digits) > 10:
        return jsonify({"ok": False, "message": "رقم الجوال يجب أن يكون 9 أو 10 أرقام."}), 400
    if len(digits) == 9 and not digits.startswith("5"):
        return jsonify({"ok": False, "message": "رقم الجوال غير صالح."}), 400
    if len(digits) == 10 and not digits.startswith("0"):
        return jsonify({"ok": False, "message": "رقم الجوال يجب أن يبدأ بـ 0."}), 400
    if len(digits) == 9:
        digits = "0" + digits  # طبّع إلى 10 أرقام

    result = _find_phone_anywhere(digits)
    if result["found"]:
        return jsonify({
            "ok": True,
            "phone": digits,
            "found": True,
            "source": result.get("source"),
            "status": result.get("status"),
            "message": result.get("hint") or "هذا الرقم مسجّل مسبقاً.",
        })

    return jsonify({"ok": True, "phone": digits, "found": False})


# ─── AJAX: POST /user/register/submit ──────────────────────────
@app.route("/user/register/submit", methods=["POST"])
def signup_submit():
    """يحفظ طلب تسجيل اشتراك جديد في DB.

    يتحقّق مرة أخرى من الرقم قبل الحفظ (طبقة أمان حتى لو تجاوز المستخدم الـ frontend).
    """
    phone = (request.form.get("phone") or "").strip()
    digits = "".join(c for c in phone if c.isdigit())
    if len(digits) == 9 and digits.startswith("5"):
        digits = "0" + digits
    if len(digits) != 10 or not digits.startswith("0"):
        return jsonify({"ok": False, "message": "رقم الجوال يجب أن يكون 10 أرقام ويبدأ بـ 0."}), 400

    # تحقّق ثاني — الرقم مش مسجّل
    check = _find_phone_anywhere(digits)
    if check["found"]:
        return jsonify({
            "ok": False,
            "message": check.get("hint") or "الرقم مسجّل مسبقاً. راجع الإدارة.",
        }), 409

    first_name = (request.form.get("first_name") or "").strip()
    second_name = (request.form.get("second_name") or "").strip()
    third_name = (request.form.get("third_name") or "").strip()
    fourth_name = (request.form.get("fourth_name") or "").strip()
    user_type = (request.form.get("user_type") or "").strip().lower()

    if not first_name or not fourth_name:
        return jsonify({"ok": False, "message": "الاسم الأول واسم العائلة مطلوبان."}), 400
    if user_type not in {"tawjihi", "university", "freelancer"}:
        return jsonify({"ok": False, "message": "اختر نوع المشترك (توجيهي / جامعي / عمل حر)."}), 400

    full_name = " ".join(p for p in [first_name, second_name, third_name, fourth_name] if p)

    # حقول اختيارية حسب النوع
    tawjihi_year = (request.form.get("tawjihi_year") or "").strip()
    tawjihi_branch = (request.form.get("tawjihi_branch") or "").strip()
    university_name = (request.form.get("university_name") or "").strip()
    university_number = (request.form.get("university_number") or "").strip()
    university_specialization = (request.form.get("university_specialization") or "").strip()
    freelancer_specialization = (request.form.get("freelancer_specialization") or "").strip()
    freelancer_company = (request.form.get("freelancer_company") or "").strip()
    notes = (request.form.get("notes") or "").strip()

    # حفظ في beneficiary_signup_requests
    try:
        execute_sql(
            """
            INSERT INTO beneficiary_signup_requests (
                phone, first_name, second_name, third_name, fourth_name, full_name,
                user_type, tawjihi_year, tawjihi_branch,
                university_name, university_number, university_specialization,
                freelancer_specialization, freelancer_company,
                notes, status
            ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,'pending')
            """,
            [
                digits, first_name, second_name, third_name, fourth_name, full_name,
                user_type, tawjihi_year, tawjihi_branch,
                university_name, university_number, university_specialization,
                freelancer_specialization, freelancer_company,
                notes,
            ],
        )
    except Exception as e:
        # الجدول قد لا يكون موجود — fallback: سجل في log_action على الأقل
        try:
            log_action(
                "signup_request_received",
                "beneficiary_signup",
                0,
                f"phone={digits} name={full_name} type={user_type} notes={notes[:60]}",
            )
        except Exception:
            pass
        return jsonify({
            "ok": True,
            "message": "تم استلام طلبك. سيتواصل معك المدير قريباً.",
            "saved_to_log_only": True,
        })

    try:
        log_action("signup_request_received", "beneficiary_signup", 0,
                   f"phone={digits} name={full_name} type={user_type}")
    except Exception:
        pass

    return jsonify({
        "ok": True,
        "message": "تم تسجيل طلبك بنجاح. سيتواصل معك المدير قريباً عبر الرقم المُسجّل.",
    })


# ─── Override صفحة /user/register بالقالب الجديد ───────────────
def _new_user_register_page():
    """صفحة تسجيل اشتراك جديدة بمسار من خطوتين."""
    return render_template("auth/user_register_v3.html")


app.view_functions["user_register"] = _new_user_register_page
