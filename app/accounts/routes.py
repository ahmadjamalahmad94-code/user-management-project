from app import legacy


accounts_page = legacy.accounts_page
add_account = legacy.add_account
edit_account = legacy.edit_account
toggle_account = legacy.toggle_account
profile_page = legacy.profile_page

ROUTES = [
    ("GET", "/accounts", "accounts_page"),
    ("GET|POST", "/accounts/add", "add_account"),
    ("GET|POST", "/accounts/edit/<int:account_id>", "edit_account"),
    ("POST", "/accounts/toggle/<int:account_id>", "toggle_account"),
    ("GET|POST", "/profile", "profile_page"),
]
