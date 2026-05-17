"""
Data Transfer Objects للـ RadiusClient.
كائنات قراءة فقط لتمثيل البطاقات، المستخدمين، الجلسات، إلخ.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass(frozen=True)
class Card:
    """بطاقة استخدام (username/password) لقطاع مدته محدد."""
    username: str
    password: str
    category_code: str           # half_hour | one_hour | two_hours | three_hours
    duration_minutes: int
    radius_profile_id: str = ""
    expires_at: datetime | None = None
    external_id: str = ""        # id داخل RADIUS عند المرحلة 2


@dataclass(frozen=True)
class UserAccount:
    """مشترك يوزر إنترنت دائم."""
    external_id: str             # id في RADIUS
    username: str
    profile_id: str = ""
    profile_name: str = ""
    is_active: bool = True
    expires_at: datetime | None = None
    quota_mb_remaining: int | None = None
    last_login_at: datetime | None = None


@dataclass(frozen=True)
class Profile:
    """باقة في RADIUS."""
    external_id: str
    name: str
    speed_up_kbps: int = 0
    speed_down_kbps: int = 0
    duration_minutes: int = 0
    quota_mb: int = 0


@dataclass(frozen=True)
class Session:
    """جلسة نشطة (متصل الآن)."""
    username: str
    nas_ip: str = ""
    session_id: str = ""
    started_at: datetime | None = None
    running_seconds: int = 0
    bytes_in: int = 0
    bytes_out: int = 0
    framed_ip: str = ""
    calling_station_id: str = ""  # MAC


@dataclass(frozen=True)
class UsageSnapshot:
    """لقطة استخدام لمشترك."""
    username: str
    total_sessions: int = 0
    total_seconds: int = 0
    total_bytes_in: int = 0
    total_bytes_out: int = 0
    last_session_at: datetime | None = None
    quota_mb_used: int = 0
    quota_mb_total: int = 0


@dataclass(frozen=True)
class PendingAction:
    """عملية في قائمة الانتظار (Phase 1 = يُنفّذها المدير يدويًا)."""
    id: int
    action_type: str
    target_kind: str = ""
    target_external_id: str = ""
    beneficiary_id: int | None = None
    payload: dict[str, Any] = field(default_factory=dict)
    status: str = "pending"
    notes: str = ""
    requested_at: datetime | None = None


@dataclass(frozen=True)
class Result:
    """نتيجة عملية تعديلية."""
    ok: bool
    message: str = ""
    pending_action_id: int | None = None  # موجود فقط في الوضع manual
    api_endpoint: str = ""                # موجود فقط في الوضع live
    data: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def pending(cls, action_id: int, message: str = "تم تسجيل العملية بانتظار تنفيذ الإدارة.") -> "Result":
        return cls(ok=True, message=message, pending_action_id=action_id)

    @classmethod
    def failure(cls, message: str) -> "Result":
        return cls(ok=False, message=message)

    @classmethod
    def success(cls, message: str = "", **data) -> "Result":
        return cls(ok=True, message=message or "تم التنفيذ.", data=dict(data))
