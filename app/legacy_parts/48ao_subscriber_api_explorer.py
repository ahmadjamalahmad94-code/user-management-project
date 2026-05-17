# 48ao_subscriber_api_explorer.py
# صفحة اختبار api المشترك (AdvClientApi) — تجرب login + كل endpoints
# وتعرض الـ raw response ليفهم المدير شو بيوفر الـ API فعلاً.
#
# المسارات:
#   GET  /admin/api/subscriber-explorer      → صفحة الاختبار
#   POST /admin/api/subscriber-explorer/run  → ينفّذ login + endpoint محدد

from flask import render_template, request, jsonify
import json as _json


@app.route("/admin/api/subscriber-explorer", methods=["GET"])
@admin_login_required
def admin_subscriber_api_explorer():
    return render_template("admin/api/subscriber_explorer.html")


@app.route("/admin/api/subscriber-explorer/run", methods=["POST"])
@admin_login_required
def admin_subscriber_api_explorer_run():
    """يجرّب login المشترك + استدعاء كل endpoints المتاحة ويرجع JSON كامل."""
    from app.services.adv_client_api import AdvClientApi, AdvClientApiError

    username = (request.form.get("username") or "").strip()
    password = (request.form.get("password") or "").strip()
    if not username or not password:
        return jsonify({"ok": False, "message": "أدخل يوزر وباسوورد المشترك."}), 400

    client = AdvClientApi.from_env()
    # الـ explorer لا يحتاج username/password من .env — المستخدم يُدخلهما بالفورم.
    # يكفي أن base_url + api_enabled موجودان.
    if not (client.config.api_enabled and client.config.base_url):
        return jsonify({
            "ok": False,
            "message": "تكامل AdvRadius Client API غير مكتمل في .env (ADV_APP_API_BASE_URL مفقود).",
            "base_url": client.config.base_url or "—",
        }), 400

    result = {
        "ok": True,
        "base_url": client.config.base_url,
        "username": username,
        "tests": [],
    }

    api_key = None
    account = None

    # 1) login
    try:
        login_data = client.login(username=username, password=password, force=True)
        api_key = login_data.get("api_key")
        account = login_data.get("account") or {}
        result["tests"].append({
            "endpoint": "/login",
            "ok": True,
            "status": "success",
            "data": {"account": account, "api_key_present": bool(api_key)},
        })
    except AdvClientApiError as e:
        result["tests"].append({
            "endpoint": "/login",
            "ok": False,
            "status": "failed",
            "error": str(e),
        })
        result["ok"] = False
        return jsonify(result)
    except Exception as e:
        result["tests"].append({
            "endpoint": "/login",
            "ok": False,
            "status": "failed",
            "error": f"{type(e).__name__}: {e}",
        })
        result["ok"] = False
        return jsonify(result)

    # 2) كل الـ endpoints المتاحة (مع البارامترات المطلوبة لكل واحد)
    endpoints = [
        ("/details",     {}),
        ("/status",      {}),
        ("/profiles",    {}),
        ("/getprofiles", {}),
        # /band يحتاج pagination params (DataTables-style)
        ("/band",        {"start": 0, "length": 10, "column": "0", "order": "desc"}),
    ]
    for path, params in endpoints:
        try:
            response = client.request(path, api_key=api_key, data=params)
            result["tests"].append({
                "endpoint": path,
                "ok": True,
                "status": "success",
                "data": response,
            })
        except AdvClientApiError as e:
            result["tests"].append({
                "endpoint": path,
                "ok": False,
                "status": "failed",
                "error": str(e),
            })
        except Exception as e:
            result["tests"].append({
                "endpoint": path,
                "ok": False,
                "status": "failed",
                "error": f"{type(e).__name__}: {e}",
            })

    return jsonify(result)
