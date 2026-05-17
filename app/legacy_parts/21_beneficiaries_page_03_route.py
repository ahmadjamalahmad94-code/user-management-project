# Beneficiaries route wrapper extracted from 21_beneficiaries_page.py. Loaded by app.legacy.

@app.route("/beneficiaries")
@login_required
@permission_required("view")
def beneficiaries_page():
    context = _beneficiaries_page_context()
    content = _beneficiaries_page_content(context)
    return render_page("????????????????????", content)
