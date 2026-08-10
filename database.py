import sqlite3
import os
from werkzeug.security import generate_password_hash, check_password_hash

PERSISTENT_DIR = "/var/data" if os.path.exists("/var/data") else os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(PERSISTENT_DIR, "database.db")

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Create Users Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'active',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create Dynamic Selectors Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS selectors (
            key_name TEXT PRIMARY KEY,
            selector_value TEXT NOT NULL
        )
    ''')
    
    # Insert Default Admin & Test Users if not exist
    cursor.execute("SELECT COUNT(*) FROM users")
    if cursor.fetchone()[0] == 0:
        admin_pass = generate_password_hash("admin123")
        emp1_pass = generate_password_hash("user123")
        emp2_pass = generate_password_hash("block123")
        
        cursor.execute("INSERT INTO users (username, password_hash, status) VALUES (?, ?, ?)", ("admin", admin_pass, "active"))
        cursor.execute("INSERT INTO users (username, password_hash, status) VALUES (?, ?, ?)", ("employee1", emp1_pass, "active"))
        cursor.execute("INSERT INTO users (username, password_hash, status) VALUES (?, ?, ?)", ("blocked_user", emp2_pass, "blocked"))
        print("[DB] Initialized default users: 'admin', 'employee1', 'blocked_user'")

    conn.commit()
    conn.close()

def authenticate_user(username, password):
    conn = get_db_connection()
    user = conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
    conn.close()
    
    if not user:
        return {"success": False, "message": "User not found"}
        
    if not check_password_hash(user["password_hash"], password):
        return {"success": False, "message": "Invalid password"}
        
    if user["status"] == "blocked":
        return {"success": False, "message": "User blocked by admin", "blocked": True}
        
    return {"success": True, "user": dict(user)}

def check_user_status(username):
    conn = get_db_connection()
    user = conn.execute("SELECT status FROM users WHERE username = ?", (username,)).fetchone()
    conn.close()
    
    if user:
        return user["status"]
    return "not_found"

def add_user(username, password, status="active"):
    conn = get_db_connection()
    pass_hash = generate_password_hash(password)
    try:
        conn.execute("INSERT INTO users (username, password_hash, status) VALUES (?, ?, ?)", (username, pass_hash, status))
        conn.commit()
        res = True
    except sqlite3.IntegrityError:
        res = False
    finally:
        conn.close()
    return res

def set_user_status(username, status):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET status = ? WHERE username = ?", (status, username))
    updated = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return updated

def get_all_users():
    conn = get_db_connection()
    users = conn.execute("SELECT id, username, status, created_at FROM users").fetchall()
    conn.close()
    return [dict(u) for u in users]
