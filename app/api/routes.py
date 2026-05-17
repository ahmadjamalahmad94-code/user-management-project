from flask import Blueprint

from app import legacy


api_bp = Blueprint("api", __name__, url_prefix="/api")

API_ROUTES = [
    ("GET", "/dashboard/live", legacy.dashboard_live_api, "dashboard_live_api"),
    ("GET", "/power-timer/status", legacy.power_timer_status_api, "power_timer_status_api"),
    ("POST", "/power-timer/start", legacy.power_timer_start_api, "power_timer_start_api"),
    ("POST", "/power-timer/pause", legacy.power_timer_pause_api, "power_timer_pause_api"),
    ("POST", "/power-timer/resume", legacy.power_timer_resume_api, "power_timer_resume_api"),
    ("POST", "/power-timer/stop", legacy.power_timer_stop_api, "power_timer_stop_api"),
]
