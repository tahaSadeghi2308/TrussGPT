from flask import request, session, Blueprint, jsonify
from app.config import USERNAME, PASSWORD
from app.utils.reset import reset_project_data


login_bp = Blueprint("login", __name__)

@login_bp.route("/api/login", methods=["POST"])
def api_login():
    data = request.get_json(silent=True) or {}
    username = data.get("username", "").strip()
    password = data.get("password", "").strip()
    
    if not username or not password:
        return jsonify({"ok": False, "errors": ["Username and password are required."]}), 400
    
    if username == USERNAME and password == PASSWORD:
        reset_project_data()
        session['logged_in'] = True
        session['username'] = username
        return jsonify({"ok": True, "message": "Login successful."})
    else:
        return jsonify({"ok": False, "errors": ["Invalid username or password."]}), 401

@login_bp.route("/api/logout", methods=["POST"])
def api_logout():
    reset_project_data()
    session.clear()
    return jsonify({"ok": True, "message": "Logged out successfully."})
