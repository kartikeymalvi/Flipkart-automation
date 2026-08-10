import sqlite3
import os
from werkzeug.security import generate_password_hash, check_password_hash

DATABASE_URL = os.environ.get("DATABASE_URL")
if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

IS_POSTGRES = bool(DATABASE_URL)

def get_db_connection():
    if IS_POSTGRES:
        import psycopg2
        import psycopg2.extras
        conn = psycopg2.connect(DATABASE_URL)
        return conn
    else:
        DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "database.db")
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    if IS_POSTGRES:
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                username VARCHAR(255) UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                status VARCHAR(50) NOT NULL DEFAULT 'active',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS selectors (
                key_name VARCHAR(255) PRIMARY KEY,
                selector_value TEXT NOT NULL
            )
        ''')
        cursor.execute("SELECT COUNT(*) FROM users")
        count = cursor.fetchone()[0]
        if count == 0:
            admin_pass = generate_password_hash("admin123")
            emp1_pass = generate_password_hash("user123")
            emp2_pass = generate_password_hash("block123")
            
            cursor.execute("INSERT INTO users (username, password_hash, status) VALUES (%s, %s, %s)", ("admin", admin_pass, "active"))
            cursor.execute("INSERT INTO users (username, password_hash, status) VALUES (%s, %s, %s)", ("employee1", emp1_pass, "active"))
            cursor.execute("INSERT INTO users (username, password_hash, status) VALUES (%s, %s, %s)", ("blocked_user", emp2_pass, "blocked"))
            print("[DB] Initialized default PostgreSQL users")
    else:
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'active',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS selectors (
                key_name TEXT PRIMARY KEY,
                selector_value TEXT NOT NULL
            )
        ''')
        cursor.execute("SELECT COUNT(*) FROM users")
        count = cursor.fetchone()[0]
        if count == 0:
            admin_pass = generate_password_hash("admin123")
            emp1_pass = generate_password_hash("user123")
            emp2_pass = generate_password_hash("block123")
            
            cursor.execute("INSERT INTO users (username, password_hash, status) VALUES (?, ?, ?)", ("admin", admin_pass, "active"))
            cursor.execute("INSERT INTO users (username, password_hash, status) VALUES (?, ?, ?)", ("employee1", emp1_pass, "active"))
            cursor.execute("INSERT INTO users (username, password_hash, status) VALUES (?, ?, ?)", ("blocked_user", emp2_pass, "blocked"))
            print("[DB] Initialized default SQLite users")

    conn.commit()
    conn.close()

def authenticate_user(username, password):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    if IS_POSTGRES:
        import psycopg2.extras
        dict_cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        dict_cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
        user = dict_cursor.fetchone()
    else:
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
    cursor = conn.cursor()
    
    if IS_POSTGRES:
        cursor.execute("SELECT status FROM users WHERE username = %s", (username,))
        row = cursor.fetchone()
        status = row[0] if row else "not_found"
    else:
        user = conn.execute("SELECT status FROM users WHERE username = ?", (username,)).fetchone()
        status = user["status"] if user else "not_found"
        
    conn.close()
    return status

def add_user(username, password, status="active"):
    conn = get_db_connection()
    cursor = conn.cursor()
    pass_hash = generate_password_hash(password)
    try:
        if IS_POSTGRES:
            cursor.execute("INSERT INTO users (username, password_hash, status) VALUES (%s, %s, %s)", (username, pass_hash, status))
        else:
            cursor.execute("INSERT INTO users (username, password_hash, status) VALUES (?, ?, ?)", (username, pass_hash, status))
        conn.commit()
        res = True
    except Exception:
        res = False
    finally:
        conn.close()
    return res

def set_user_status(username, status):
    conn = get_db_connection()
    cursor = conn.cursor()
    if IS_POSTGRES:
        cursor.execute("UPDATE users SET status = %s WHERE username = %s", (status, username))
    else:
        cursor.execute("UPDATE users SET status = ? WHERE username = ?", (status, username))
    updated = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return updated

def get_all_users():
    conn = get_db_connection()
    if IS_POSTGRES:
        import psycopg2.extras
        dict_cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        dict_cursor.execute("SELECT id, username, status, created_at FROM users")
        rows = dict_cursor.fetchall()
        result = [dict(u) for u in rows]
        # format timestamp
        for r in result:
            if r.get("created_at"):
                r["created_at"] = str(r["created_at"])
    else:
        users = conn.execute("SELECT id, username, status, created_at FROM users").fetchall()
        result = [dict(u) for u in users]
        
    conn.close()
    return result
