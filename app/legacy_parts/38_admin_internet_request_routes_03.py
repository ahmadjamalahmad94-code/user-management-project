# Continued split from 38_admin_internet_request_routes.py lines 263-307. Loaded by app.legacy.


@app.route("/admin/internet-requests/<int:request_id>/reject", methods=["POST"])
@login_required
@permission_required("approve_internet_requests")
def admin_internet_request_reject(request_id):
    row = get_internet_request_row(request_id)
    if not row:
        flash("الطلب غير موجود.", "error")
        return redirect(url_for("admin_internet_requests_page"))
    reason = clean_csv_value(request.form.get("reason")) or "تم رفض الطلب من الإدارة."
    update_internet_service_request(
        request_id,
        status="rejected",
        reviewed_by=session.get("username", ""),
        reviewed_at=now_local(),
        error_message=reason,
    )
    log_action("reject_internet_request", "internet_request", request_id, reason)
    try:
        from app.services.notification_service import notify_internet_request_status
        notify_internet_request_status(request_id, "rejected", actor_name=session.get("username", ""), reason=reason)
    except Exception:
        pass
    flash("تم رفض الطلب.", "success")
    return redirect(url_for("admin_request_center_detail", source="internet", request_id=request_id))


@app.route("/admin/internet-requests/<int:request_id>/execute", methods=["POST"])
@login_required
@permission_required("execute_radius_actions")
def admin_internet_request_execute(request_id):
    row = get_internet_request_row(request_id)
    if not row:
        flash("الطلب غير موجود.", "error")
        return redirect(url_for("admin_internet_requests_page"))
    try:
        endpoint, _response = execute_internet_service_request_row(row)
        try:
            from app.services.notification_service import notify_internet_request_status
            notify_internet_request_status(request_id, "executed", actor_name=session.get("username", ""))
        except Exception:
            pass
        flash(f"تم تنفيذ الطلب بنجاح عبر {endpoint}.", "success")
    except Exception as exc:
        update_internet_service_request(
            request_id,
            status="failed",
            api_response={"error": str(exc)},
            error_message=str(exc),
            executed_at=now_local(),
        )
        log_action("execute_radius_action_failed", "internet_request", request_id, str(exc))
        try:
            from app.services.notification_service import notify_internet_request_status
            notify_internet_request_status(request_id, "failed", actor_name=session.get("username", ""), reason=str(exc))
        except Exception:
            pass
        flash(f"فشل تنفيذ الطلب: {safe(str(exc))}", "error")
    return redirect(url_for("admin_request_center_detail", source="internet", request_id=request_id))
