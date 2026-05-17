"""
access_rules — قواعد ربط نوع المشترك (user_type) بأنواع الوصول المسموحة.

القاعدة:
  - توجيهي (tawjihi)   → بطاقات فقط
  - جامعي (university) → بطاقات أو يوزر
  - عمل حر (freelancer)→ بطاقات أو يوزر

تستخدم في:
  - بوابة المشترك: عرض الفئات المتاحة + رفض الطلبات غير المسموحة
  - الإدارة: عند تحويل مشترك من cards ↔ username (إن حاول المدير وضع
    توجيهي في وضع username يُمنع)
  - quota_engine: فحص إضافي قبل السماح بطلب بطاقة
"""
from __future__ import annotations

from typing import Iterable


# الثوابت
CARDS = "cards"
USERNAME = "username"

# قاموس القاعدة: لكل user_type ما هي أنواع الوصول المسموحة
ACCESS_MATRIX: dict[str, tuple[str, ...]] = {
    "tawjihi":    (CARDS,),                # توجيهي: بطاقات فقط
    "university": (CARDS, USERNAME),       # جامعي: الاثنان
    "freelancer": (CARDS, USERNAME),       # عمل حر: الاثنان
}

# الافتراضي عند التسجيل (للجميع)
DEFAULT_ACCESS_MODE = CARDS

# التسميات للعرض
ACCESS_LABELS = {
    CARDS:    "نظام البطاقات",
    USERNAME: "يوزر إنترنت دائم",
}

USER_TYPE_LABELS = {
    "tawjihi":    "توجيهي",
    "university": "جامعي",
    "freelancer": "عمل حر",
}

# قواعد فئات البطاقات المسموحة لكل نوع مشترك (hard-coded — تغلب على السياسات)
# توجيهي = نصف ساعة فقط — قاعدة صارمة لا يمكن تجاوزها عبر سياسة
USER_TYPE_CARD_CATEGORY_RULES: dict[str, tuple[str, ...] | None] = {
    "tawjihi": ("half_hour",),
    # الباقي بدون قيد خاص — تخضع للسياسة فقط
}


# ─── دوال القاعدة ────────────────────────────────────────────────────
def allowed_access_modes(user_type: str) -> tuple[str, ...]:
    """الـ access modes المسموحة لـ user_type معين."""
    if not user_type:
        return (CARDS,)
    return ACCESS_MATRIX.get(user_type.strip().lower(), (CARDS,))


def is_access_mode_allowed(user_type: str, access_mode: str) -> bool:
    """هل يحق لمشترك بنوع X استخدام access_mode معين؟"""
    return access_mode in allowed_access_modes(user_type)


def default_access_mode_for(user_type: str) -> str:
    """الـ access_mode الافتراضي لنوع مشترك."""
    allowed = allowed_access_modes(user_type)
    return allowed[0] if allowed else CARDS


def can_switch_to(user_type: str, target_mode: str) -> tuple[bool, str]:
    """
    هل يمكن تحويل مشترك بنوع user_type إلى target_mode؟
    يرجع (True, "") أو (False, "سبب الرفض").
    """
    if not is_access_mode_allowed(user_type, target_mode):
        ut_label = USER_TYPE_LABELS.get(user_type, user_type)
        am_label = ACCESS_LABELS.get(target_mode, target_mode)
        return False, f"المشترك ({ut_label}) لا يمكن تحويله إلى {am_label} وفق قواعد النظام."
    return True, ""


def describe_rules() -> list[dict]:
    """يرجع وصفًا للعرض في الـ UI."""
    return [
        {
            "user_type": ut,
            "label": USER_TYPE_LABELS[ut],
            "allowed_modes": [ACCESS_LABELS[m] for m in modes],
            "is_locked": len(modes) == 1,
        }
        for ut, modes in ACCESS_MATRIX.items()
    ]


def allowed_card_codes_for_user_type(user_type: str) -> tuple[str, ...] | None:
    """يرجع قائمة أكواد فئات البطاقات المسموحة لنوع المشترك.
    يقرأ أولاً من جدول user_type_card_rules (قابل للتعديل من الإدارة).
    إذا الجدول فاضي أو غير متاح → يستخدم الافتراضي المُبرمج.
    None = الكل مسموح (تخضع للسياسة فقط).
    """
    if not user_type:
        return None
    ut = user_type.strip().lower()
    # 1) جرّب القراءة من DB (قابل للتعديل من الإدارة)
    try:
        from app import legacy as _legacy
        row = _legacy.query_one(
            "SELECT allowed_codes_csv FROM user_type_card_rules WHERE user_type=%s",
            [ut],
        )
        if row is not None:
            csv_val = (row.get("allowed_codes_csv") or "").strip()
            if not csv_val:
                return None  # الكل مسموح
            return tuple(c.strip().lower() for c in csv_val.split(",") if c.strip())
    except Exception:
        pass
    # 2) Fallback للقاموس المُبرمج
    return USER_TYPE_CARD_CATEGORY_RULES.get(ut)


def whatsapp_group_url_for_user_type(user_type: str) -> str:
    """يرجع رابط مجموعة واتساب المربوطة بنوع المشترك، أو نصًا فارغًا."""
    if not user_type:
        return ""
    try:
        from app import legacy as _legacy
        row = _legacy.query_one(
            "SELECT whatsapp_group_url FROM user_type_card_rules WHERE user_type=%s",
            [user_type.strip().lower()],
        )
        url = ((row or {}).get("whatsapp_group_url") or "").strip()
        if url.startswith(("chat.whatsapp.com/", "wa.me/")):
            url = "https://" + url
        if url.startswith(("https://", "http://")):
            return url
    except Exception:
        pass
    return ""


def is_card_category_allowed_for_user_type(user_type: str, category_code: str) -> bool:
    """هل يحقّ لنوع مشترك معين أخذ فئة بطاقات معينة؟"""
    allowed = allowed_card_codes_for_user_type(user_type)
    if allowed is None:
        return True
    return (category_code or "").strip().lower() in allowed


def filter_allowed_categories(user_type: str, categories: Iterable[dict]) -> list[dict]:
    """
    يرجع الفئات المسموحة لنوع المشترك بعد تطبيق:
    1. قاعدة access_mode (لو ما يسمح ببطاقات أصلًا → قائمة فارغة).
    2. قاعدة USER_TYPE_CARD_CATEGORY_RULES (مثلاً توجيهي → نصف ساعة فقط).
    """
    if CARDS not in allowed_access_modes(user_type):
        return []
    allowed_codes = allowed_card_codes_for_user_type(user_type)
    if allowed_codes is None:
        return list(categories)
    return [c for c in categories if (c.get("code") or "").strip().lower() in allowed_codes]
