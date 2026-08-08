import os
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import database

app = Flask(__name__)
CORS(app)

# Initialize SQLite database on startup
database.init_db()

# Server App Version Config
CURRENT_VERSION = "3.1"
MANDATORY_UPDATE = True
RELEASE_NOTES = "1. test update"

UPDATES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static", "updates")
os.makedirs(UPDATES_DIR, exist_ok=True)

# ==========================================
# 🔐 AUTHENTICATION ENDPOINTS
# ==========================================
@app.route("/api/login/", methods=["POST"])
def login():
    data = request.get_json() or {}
    username = data.get("username", "").strip()
    password = data.get("password", "").strip()

    if not username or not password:
        return jsonify({"status": "failed", "message": "Username and password required"}), 400

    result = database.authenticate_user(username, password)
    
    if result.get("success"):
        return jsonify({
            "status": "success",
            "token": f"auth_token_{username}",
            "user": username
        })
    elif result.get("blocked"):
        return jsonify({
            "status": "blocked",
            "message": "Account blocked by admin!"
        }), 403
    else:
        return jsonify({
            "status": "failed",
            "message": result.get("message", "Invalid credentials")
        }), 401

@app.route("/api/verify-user/", methods=["POST"])
def verify_user():
    data = request.get_json() or {}
    username = data.get("username", "").strip()

    if not username:
        return jsonify({"status": "failed", "message": "Username required"}), 400

    status = database.check_user_status(username)

    if status == "active":
        return jsonify({"status": "success"})
    elif status == "blocked":
        return jsonify({"status": "blocked", "message": "User blocked"}), 403
    else:
        return jsonify({"status": "failed", "message": "User not found"}), 404

# ==========================================
# 🔄 OTA AUTO-UPDATER ENDPOINT
# ==========================================
@app.route("/api/check-update/", methods=["GET"])
def check_update():
    return jsonify({
        "status": "success",
        "version": CURRENT_VERSION,
        "is_mandatory": MANDATORY_UPDATE,
        "download_link": f"{request.host_url}static/updates/FlipkartBot_v{CURRENT_VERSION}.zip",
        "release_notes": RELEASE_NOTES
    })

@app.route("/static/updates/<path:filename>")
def serve_update_file(filename):
    return send_from_directory(UPDATES_DIR, filename)

# ==========================================
# ☁️ DYNAMIC CLOUD SELECTORS API
# ==========================================
@app.route("/selectors/", methods=["GET"])
@app.route("/api/locators/", methods=["GET"])
def get_selectors():
    return jsonify({
        "navbar_cart_icon": "//a[contains(@href, '/viewcart') and contains(., 'Cart')]",
        "cart_remove_btn": "//div[text()='Remove' or text()='REMOVE']",
        "cart_remove_confirm": "//div[text()='Remove' or text()='REMOVE']",
        "add_to_cart_svg": "svg:has(g[clip-path*='AddToCart']), svg:has(defs clipPath[id*='AddToCart'])",
        "apply_btn_text": "Add Coupon",
        "coupon_input": "input[maxlength='50']"
    })

# ==========================================
# ⚙️ ADMIN USER MANAGEMENT ENDPOINTS
# ==========================================
@app.route("/admin/users/", methods=["GET"])
def list_users():
    users = database.get_all_users()
    return jsonify({"status": "success", "users": users})

@app.route("/admin/add-user/", methods=["POST"])
def add_user():
    data = request.get_json() or {}
    username = data.get("username")
    password = data.get("password")
    
    if not username or not password:
        return jsonify({"status": "failed", "message": "Username & Password required"}), 400
        
    success = database.add_user(username, password)
    if success:
        return jsonify({"status": "success", "message": f"User '{username}' created successfully!"})
    else:
        return jsonify({"status": "failed", "message": "Username already exists"}), 400

@app.route("/admin/block-user/", methods=["POST"])
def block_user():
    data = request.get_json() or {}
    username = data.get("username")
    action = data.get("action", "block") # "block" or "unblock"
    
    new_status = "blocked" if action == "block" else "active"
    updated = database.set_user_status(username, new_status)
    
    if updated:
        return jsonify({"status": "success", "message": f"User '{username}' is now {new_status}"})
    else:
        return jsonify({"status": "failed", "message": "User not found"}), 404

if __name__ == "__main__":
    print("[SERVER] SaaS Backend Server running on http://127.0.0.1:5000")
    app.run(host="0.0.0.0", port=5000, debug=True)
