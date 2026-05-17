# 48aa_phase3_tiers.py
# Phase 3 — منطق مستويات السماح والتوثيق الزمني
# يوفّر:
#   - allowed_hours_for_beneficiary(b)  → قائمة المدد المسموحة بالساعات حسب مستوى السماح
#   - auto_expire_verifications()       → تخفيض كل من انتهى verified_until إلى reviewed
#   - context processor لتمرير المعلومات للقوالب

from datetime import datetime


# الخريطة الأساسية: المدد المسموحة لكل مستوى سماح (بالدقائق)
TIER_DURATIONS_MIN = {
    "basic":    [30],                      # أساسي — نصف ساعة فقط
    "standard": [30, 60, 120],             # موسّع — حتى ساعتين
    "complete": [30, 60, 120, 180],        # متقدم — حتى 3 ساعات
    "super":    [30, 60, 120, 180, 240],   # خاص — حتى 4 ساعات
}

TIER_LABELS = {
    "basic":    "أساسي",
    "standard": "موسّع",
    "complete": "متقدم",
    "super":    "خاص",
}


def get_effective_tier(beneficiary):
    """يرجع مستوى السماح الفعلي بعد فحص صلاحية التوثيق الزمني.
       لو verified_until فات تاريخه → يهبط للمستوى الموسّع تلقائياً (يعرض فقط، لا يكتب)."""
    if not beneficiary:
        return "basic"
    tier = (beneficiary.get("tier") or "basic")
    vu = beneficiary.get("verified_until")
    # إذا كان للحساب تاريخ انتهاء وفات
    if vu:
        try:
            if hasattr(vu, "year"):  # date/datetime
                expired = vu < datetime.now().date() if hasattr(vu, "day") and not hasattr(vu, "hour") else vu < datetime.now()
            else:  # string YYYY-MM-DD
                expired = str(vu) < datetime.now().strftime("%Y-%m-%d")
        except Exception:
            expired = False
        if expired and tier in ("complete", "super"):
            tier = "standard"
    return tier if tier in TIER_DURATIONS_MIN else "basic"


def allowed_hours_for_beneficiary(beneficiary):
    """يرجع قائمة الدقائق المسموحة (مرتبة) حسب مستوى السماح الفعلي."""
    return TIER_DURATIONS_MIN.get(get_effective_tier(beneficiary), [30])


def can_request_minutes(beneficiary, minutes):
    """التحقق سيرفر-سايد قبل إنشاء طلب إنترنت بمدة معينة."""
    try:
        m = int(minutes)
    except (TypeError, ValueError):
        return False
    return m in allowed_hours_for_beneficiary(beneficiary)


# ────────────────────────────────────────────────────────────────
# Auto-expire — يُستدعى عند تحميل أي صفحة (cheap query)
# ────────────────────────────────────────────────────────────────
def auto_expire_verifications():
    """خفّض verified→reviewed لمن انتهت صلاحياتهم. آمن لو الأعمدة غير موجودة.
       نسجّل أي فشل حقيقي بدل ابتلاعه (يساعد على تشخيص schema mismatches)."""
    import logging
    from datetime import datetime
    log = logging.getLogger("hobehub.phase3_tiers")
    today = datetime.now().strftime("%Y-%m-%d")
    try:
        execute_sql(
            """
            UPDATE beneficiaries SET
                verification_status='reviewed',
                tier='standard'
            WHERE verified_until IS NOT NULL
              AND verified_until < %s
              AND verification_status IN ('verified','super')
            """,
            [today],
        )
    except Exception as e:
        msg = str(e).lower()
        # حقول مفقودة: عادي لو schema bootstrap ما اشتغل بعد على هذه القاعدة
        if "no such column" in msg or "column" in msg and "does not exist" in msg:
            log.info("auto_expire_verifications skipped (columns not bootstrapped yet)")
        else:
            log.warning("auto_expire_verifications failed: %s", e)


# نستدعيها مرّة عند تحميل التطبيق (cron خفيف)
auto_expire_verifications()


# ────────────────────────────────────────────────────────────────
# Context processor — يخلي القوالب تشوف مستوى السماح للمستخدم الحالي
# ────────────────────────────────────────────────────────────────
@app.context_processor
def _inject_tier_helpers():
    return {
        "TIER_DURATIONS_MIN": TIER_DURATIONS_MIN,
        "TIER_LABELS": TIER_LABELS,
        "get_effective_tier": get_effective_tier,
        "allowed_hours_for_beneficiary": allowed_hours_for_beneficiary,
    }
