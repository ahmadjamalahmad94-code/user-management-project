# Auto-split from app/legacy.py lines 2520-2570. Loaded by app.legacy.
USER_BASE_TEMPLATE = _legacy_template_text('14_user_base_template.USER_BASE_TEMPLATE.html')


def render_user_page(title, content):
    return render_template_string(USER_BASE_TEMPLATE, title=title, content=content)
