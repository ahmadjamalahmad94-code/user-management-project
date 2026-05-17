from app import legacy


beneficiaries_page = legacy.beneficiaries_page
add_beneficiary_page = legacy.app.view_functions["add_beneficiary_page"]
edit_beneficiary_page = legacy.edit_beneficiary_page
delete_beneficiary = legacy.delete_beneficiary
add_usage = legacy.add_usage
reset_weekly_usage = legacy.app.view_functions["reset_weekly_usage"]
bulk_delete_beneficiaries = legacy.bulk_delete_beneficiaries
export_selected_beneficiaries = legacy.export_selected_beneficiaries

ROUTES = [
    ("GET", "/beneficiaries", "beneficiaries_page"),
    ("GET|POST", "/beneficiaries/add", "add_beneficiary_page"),
    ("GET|POST", "/beneficiaries/edit/<int:beneficiary_id>", "edit_beneficiary_page"),
    ("POST", "/beneficiaries/delete/<int:beneficiary_id>", "delete_beneficiary"),
    ("POST", "/beneficiaries/add_usage/<int:beneficiary_id>", "add_usage"),
    ("POST", "/beneficiaries/reset-weekly-usage", "reset_weekly_usage"),
    ("POST", "/beneficiaries/bulk-delete", "bulk_delete_beneficiaries"),
    ("POST", "/beneficiaries/export-selected", "export_selected_beneficiaries"),
]
