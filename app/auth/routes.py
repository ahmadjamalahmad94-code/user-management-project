from app import legacy


login = legacy.login
logout = legacy.logout

ROUTES = [
    ("GET|POST", "/login", "login"),
    ("GET", "/logout", "logout"),
]
