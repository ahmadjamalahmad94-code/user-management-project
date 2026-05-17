@app.route("/portal/power-timer/status")
def portal_power_timer_status_api():
    if not session.get("account_id") and not session.get("beneficiary_id"):
        return jsonify({"ok": False, "message": "LOGIN_REQUIRED"}), 401
    return jsonify(build_power_timer_status())
