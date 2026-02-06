import sqlite3
import hashlib
import pandas as pd
import os
import json
import uuid

DB_FILE = os.path.join("data", "gapgpt.db")


def init_db():
    if not os.path.exists("data"):
        os.makedirs("data")

    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()

    c.execute('''CREATE TABLE IF NOT EXISTS users (
                    username TEXT PRIMARY KEY,
                    password TEXT,
                    balance REAL,
                    role TEXT
                )''')

    c.execute('''CREATE TABLE IF NOT EXISTS logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT,
                    model TEXT,
                    type TEXT,
                    cost_toman REAL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )''')

    c.execute('''CREATE TABLE IF NOT EXISTS payment_requests (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT,
                    amount INTEGER,
                    receipt_img BLOB,
                    status TEXT DEFAULT "PENDING",
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )''')

    c.execute('''CREATE TABLE IF NOT EXISTS bank_accounts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    bank_name TEXT,
                    owner_name TEXT,
                    card_number TEXT,
                    sheba_number TEXT
                )''')

    c.execute('''CREATE TABLE IF NOT EXISTS sessions (
                    session_id TEXT PRIMARY KEY,
                    username TEXT,
                    title TEXT,
                    messages TEXT,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )''')

    c.execute("SELECT * FROM users WHERE username = 'admin'")
    if not c.fetchone():
        hashed_pw = hashlib.sha256("admin123".encode()).hexdigest()
        c.execute("INSERT INTO users VALUES (?, ?, ?, ?)", ("admin", hashed_pw, 5000000.0, "admin"))

    conn.commit()
    conn.close()


# --- USER FUNCTIONS ---
def create_user(username, password, balance=0):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    try:
        hashed_pw = hashlib.sha256(password.encode()).hexdigest()
        c.execute("INSERT INTO users VALUES (?, ?, ?, ?)", (username, hashed_pw, balance, "user"))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()


def get_user(username):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE username = ?", (username,))
    user = c.fetchone()
    conn.close()
    return user


def update_user_password(username, new_password):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    try:
        hashed_pw = hashlib.sha256(new_password.encode()).hexdigest()
        c.execute("UPDATE users SET password = ? WHERE username = ?", (hashed_pw, username))
        conn.commit()
        return True
    except Exception:
        return False
    finally:
        conn.close()


def delete_user(username):
    if username == "admin":
        return False
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("DELETE FROM users WHERE username = ?", (username,))
    conn.commit()
    conn.close()
    return True


def update_balance(username, amount):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("UPDATE users SET balance = balance + ? WHERE username = ?", (amount, username))
    conn.commit()
    conn.close()


def get_all_users_df():
    conn = sqlite3.connect(DB_FILE)
    df = pd.read_sql_query("SELECT username, balance, role FROM users", conn)
    conn.close()
    return df


# --- LOGS & EXTRAS ---
def log_usage(username, model, type_usage, cost):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("INSERT INTO logs (username, model, type, cost_toman) VALUES (?, ?, ?, ?)",
              (username, model, type_usage, cost))
    conn.commit()
    conn.close()


def get_logs_df():
    conn = sqlite3.connect(DB_FILE)
    df = pd.read_sql_query("SELECT * FROM logs ORDER BY id DESC LIMIT 100", conn)
    conn.close()
    return df


# --- FINANCIAL ---
def submit_payment_request(username, amount, receipt_bytes):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("INSERT INTO payment_requests (username, amount, receipt_img, status) VALUES (?, ?, ?, ?)",
              (username, amount, receipt_bytes, "PENDING"))
    conn.commit()
    conn.close()


def get_pending_payments():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT id, username, amount, receipt_img, created_at FROM payment_requests WHERE status = 'PENDING' ORDER BY created_at ASC")
    rows = c.fetchall()
    conn.close()
    return rows


def process_payment_request(request_id, action):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT username, amount FROM payment_requests WHERE id = ?", (request_id,))
    req = c.fetchone()
    if req:
        user, amount = req
        c.execute("UPDATE payment_requests SET status = ? WHERE id = ?", (action, request_id))
        if action == "APPROVED":
            c.execute("UPDATE users SET balance = balance + ? WHERE username = ?", (amount, user))
        conn.commit()
        conn.close()
        return True
    conn.close()
    return False


# --- BANKING ---
def add_bank_account(bank_name, owner_name, card_number, sheba_number):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("INSERT INTO bank_accounts (bank_name, owner_name, card_number, sheba_number) VALUES (?, ?, ?, ?)",
              (bank_name, owner_name, card_number, sheba_number))
    conn.commit()
    conn.close()


def delete_bank_account(account_id):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("DELETE FROM bank_accounts WHERE id = ?", (account_id,))
    conn.commit()
    conn.close()


def get_bank_accounts():
    conn = sqlite3.connect(DB_FILE)
    df = pd.read_sql_query("SELECT * FROM bank_accounts", conn)
    conn.close()
    return df


# --- CHAT SESSIONS ---
def create_new_session(username, first_message=""):
    session_id = str(uuid.uuid4())
    title = first_message[:30] + "..." if len(first_message) > 30 else (first_message or "گفتگوی جدید")
    messages_json = json.dumps([])
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("INSERT INTO sessions (session_id, username, title, messages) VALUES (?, ?, ?, ?)",
              (session_id, username, title, messages_json))
    conn.commit()
    conn.close()
    return session_id


def save_session_messages(session_id, messages):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    messages_json = json.dumps(messages, ensure_ascii=False)
    c.execute("UPDATE sessions SET messages = ?, updated_at = CURRENT_TIMESTAMP WHERE session_id = ?",
              (messages_json, session_id))
    conn.commit()
    conn.close()


def get_user_sessions(username):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT session_id, title, updated_at FROM sessions WHERE username = ? ORDER BY updated_at DESC", (username,))
    rows = c.fetchall()
    conn.close()
    return rows


def load_session_messages(session_id):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT messages FROM sessions WHERE session_id = ?", (session_id,))
    row = c.fetchone()
    conn.close()
    if row:
        try:
            return json.loads(row[0])
        except json.JSONDecodeError:
            return []
    return []


def delete_session(session_id):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("DELETE FROM sessions WHERE session_id = ?", (session_id,))
    conn.commit()
    conn.close()