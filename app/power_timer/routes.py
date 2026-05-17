from app import legacy


power_timer_page = legacy.power_timer_page

ROUTES = [
    ("GET", "/timer", "power_timer_page"),
]
