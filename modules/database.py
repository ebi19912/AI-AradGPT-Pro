# modules/database.py
"""
ماژول مدیریت پایگاه داده SQLite با تنظیمات همزمانی (WAL Mode) و پشتیبانی از
کاربران، گزارشات، سشن‌ها، تراکنش‌های مالی، تنظیمات سیستم و تاریخچه تصاویر.
"""

import sqlite3
import hashlib
import pandas as pd
import os
import json
import uuid
from typing import Optional, List, Dict, Any, Tuple

DB_FOLDER = "data"
DB_FILE = os.path.join(DB_FOLDER, "gapgpt.db")


def get_connection() -> sqlite3.Connection:
    """
    ایجاد اتصال به پایگاه‌داده با تنظیمات امن همزمانی (WAL Mode و Timeout بالا)
    برای جلوگیری از خطای Database Locked در محیط‌های چندکاربره
    """
    if not os.path.exists(DB_FOLDER):
        os.makedirs(DB_FOLDER, exist_ok=True)

    conn = sqlite3.connect(DB_FILE, timeout=30.0)
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA busy_timeout=30000;")
    return conn


def init_db():
    """راه‌اندازی ساختار جداول پایگاه‌داده و ایجاد کاربر و تنظیمات پیش‌فرض"""
    conn = get_connection()
    c = conn.cursor()

    # 1. جدول کاربران
    c.execute('''CREATE TABLE IF NOT EXISTS users (
                    username TEXT PRIMARY KEY,
                    password TEXT,
                    balance REAL DEFAULT 0,
                    role TEXT DEFAULT 'user',
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )''')

    # 2. جدول لاگ مصرف و هزینه‌ها
    c.execute('''CREATE TABLE IF NOT EXISTS logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT,
                    model TEXT,
                    type TEXT,
                    cost_toman REAL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )''')

    # 3. جدول درخواست‌های شارژ کیف پول
    c.execute('''CREATE TABLE IF NOT EXISTS payment_requests (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT,
                    amount INTEGER,
                    receipt_img BLOB,
                    status TEXT DEFAULT "PENDING",
                    admin_note TEXT DEFAULT "",
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )''')

    # 4. جدول حساب‌های بانکی سیستم
    c.execute('''CREATE TABLE IF NOT EXISTS bank_accounts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    bank_name TEXT,
                    owner_name TEXT,
                    card_number TEXT,
                    sheba_number TEXT
                )''')

    # 5. جدول سشن‌های گفتگو
    c.execute('''CREATE TABLE IF NOT EXISTS sessions (
                    session_id TEXT PRIMARY KEY,
                    username TEXT,
                    title TEXT,
                    messages TEXT,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )''')

    # 6. جدول تنظیمات سراسری سیستم (Settings)
    c.execute('''CREATE TABLE IF NOT EXISTS settings (
                    key TEXT PRIMARY KEY,
                    value TEXT
                )''')

    # 7. جدول تاریخچه تصاویر تولید شده
    c.execute('''CREATE TABLE IF NOT EXISTS images_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT,
                    prompt TEXT,
                    image_url TEXT,
                    model TEXT,
                    cost REAL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )''')

    # بررسی ستون‌های احتمالی برای بروزرسانی ساختار جداول قدیمی
    try:
        c.execute("ALTER TABLE payment_requests ADD COLUMN admin_note TEXT DEFAULT ''")
    except Exception:
        pass

    try:
        c.execute("ALTER TABLE users ADD COLUMN created_at DATETIME DEFAULT CURRENT_TIMESTAMP")
    except Exception:
        pass

    # بررسی و ایجاد حساب ادمین در صورت عدم وجود
    c.execute("SELECT * FROM users WHERE username = 'admin'")
    if not c.fetchone():
        hashed_pw = hashlib.sha256("admin123".encode()).hexdigest()
        c.execute("INSERT INTO users (username, password, balance, role) VALUES (?, ?, ?, ?)",
                  ("admin", hashed_pw, 5000000.0, "admin"))

    # تنظیمات پیش‌فرض سیستم در صورت خالی بودن
    default_settings = {
        "ACTIVE_PROVIDER": "openrouter",
        "USD_TO_TOMAN": "85000",
        "WELCOME_BONUS": "20000",
        "APP_TITLE": "AradGPT Pro",
        "ENABLE_REGISTRATION": "true"
    }
    for k, v in default_settings.items():
        c.execute("INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)", (k, v))

    conn.commit()
    conn.close()


# ==========================================
# --- 1. USER FUNCTIONS (مدیریت کاربران) ---
# ==========================================
def hash_password(password: str) -> str:
    """تولید هش SHA-256 برای گذرواژه"""
    return hashlib.sha256(password.encode()).hexdigest()


def create_user(username: str, password: str, balance: float = 0, role: str = "user") -> bool:
    """ایجاد یک کاربر جدید در سیستم"""
    username = username.strip().lower()
    if not username or not password:
        return False
    conn = get_connection()
    c = conn.cursor()
    try:
        hashed_pw = hash_password(password)
        c.execute("INSERT INTO users (username, password, balance, role) VALUES (?, ?, ?, ?)",
                  (username, hashed_pw, float(balance), role))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()


def get_user(username: str):
    """دریافت اطلاعات یک کاربر با نام کاربری"""
    if not username:
        return None
    username = username.strip().lower()
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT username, password, balance, role, created_at FROM users WHERE username = ?", (username,))
    user = c.fetchone()
    conn.close()
    return user


def update_user_password(username: str, new_password: str) -> bool:
    """تغییر گذرواژه کاربر"""
    if not username or not new_password:
        return False
    username = username.strip().lower()
    conn = get_connection()
    c = conn.cursor()
    try:
        hashed_pw = hash_password(new_password)
        c.execute("UPDATE users SET password = ? WHERE username = ?", (hashed_pw, username))
        conn.commit()
        return True
    except Exception:
        return False
    finally:
        conn.close()


def update_user_role(username: str, new_role: str) -> bool:
    """تغییر نقش کاربر (user / admin)"""
    if not username or username == "admin":
        return False
    username = username.strip().lower()
    conn = get_connection()
    c = conn.cursor()
    try:
        c.execute("UPDATE users SET role = ? WHERE username = ?", (new_role, username))
        conn.commit()
        return True
    except Exception:
        return False
    finally:
        conn.close()


def delete_user(username: str) -> bool:
    """حذف کاربر (ادمین اصلی قابل حذف نیست)"""
    username = username.strip().lower()
    if username == "admin":
        return False
    conn = get_connection()
    c = conn.cursor()
    try:
        c.execute("DELETE FROM users WHERE username = ?", (username,))
        c.execute("DELETE FROM sessions WHERE username = ?", (username,))
        conn.commit()
        return True
    except Exception:
        return False
    finally:
        conn.close()


def update_balance(username: str, amount: float):
    """افزایش یا کاهش موجودی کاربر"""
    username = username.strip().lower()
    conn = get_connection()
    c = conn.cursor()
    c.execute("UPDATE users SET balance = balance + ? WHERE username = ?", (float(amount), username))
    conn.commit()
    conn.close()


def get_all_users_df() -> pd.DataFrame:
    """دریافت لیست تمام کاربران به صورت DataFrame"""
    conn = get_connection()
    df = pd.read_sql_query("SELECT username, balance, role, created_at FROM users ORDER BY created_at DESC", conn)
    conn.close()
    return df


# ==========================================
# --- 2. LOGS & USAGE (لاگ مصرف) ---
# ==========================================
def log_usage(username: str, model: str, type_usage: str, cost: float):
    """ثبت لاگ مصرف خدمات هوش مصنوعی"""
    username = username.strip().lower()
    conn = get_connection()
    c = conn.cursor()
    c.execute("INSERT INTO logs (username, model, type, cost_toman) VALUES (?, ?, ?, ?)",
              (username, model, type_usage, float(cost)))
    conn.commit()
    conn.close()


def get_logs_df(limit: int = 500) -> pd.DataFrame:
    """دریافت آخرین لاگ‌های سیستم"""
    conn = get_connection()
    df = pd.read_sql_query(f"SELECT * FROM logs ORDER BY id DESC LIMIT {int(limit)}", conn)
    conn.close()
    return df


def get_user_logs_df(username: str, limit: int = 50) -> pd.DataFrame:
    """دریافت لاگ‌های یک کاربر خاص"""
    username = username.strip().lower()
    conn = get_connection()
    df = pd.read_sql_query(
        "SELECT id, model, type, cost_toman, timestamp FROM logs WHERE username = ? ORDER BY id DESC LIMIT ?",
        conn, params=(username, limit)
    )
    conn.close()
    return df


# ==========================================
# --- 3. FINANCIAL & PAYMENTS (مالی و واریز) ---
# ==========================================
def submit_payment_request(username: str, amount: int, receipt_bytes: Optional[bytes]):
    """ثبت درخواست شارژ با فیش واریزی"""
    username = username.strip().lower()
    conn = get_connection()
    c = conn.cursor()
    c.execute("INSERT INTO payment_requests (username, amount, receipt_img, status) VALUES (?, ?, ?, ?)",
              (username, int(amount), receipt_bytes, "PENDING"))
    conn.commit()
    conn.close()


def get_pending_payments():
    """دریافت درخواست‌های شارژ در انتظار تایید"""
    conn = get_connection()
    c = conn.cursor()
    c.execute("""SELECT id, username, amount, receipt_img, created_at, admin_note 
                 FROM payment_requests 
                 WHERE status = 'PENDING' 
                 ORDER BY created_at ASC""")
    rows = c.fetchall()
    conn.close()
    return rows


def get_all_payment_requests(limit: int = 100):
    """دریافت تاریخچه تمام درخواست‌های شارژ برای ادمین"""
    conn = get_connection()
    df = pd.read_sql_query(
        f"SELECT id, username, amount, status, admin_note, created_at FROM payment_requests ORDER BY id DESC LIMIT {int(limit)}",
        conn
    )
    conn.close()
    return df


def get_user_payment_requests(username: str) -> pd.DataFrame:
    """دریافت سابقه و وضعیت درخواست‌های شارژ یک کاربر"""
    username = username.strip().lower()
    conn = get_connection()
    df = pd.read_sql_query(
        "SELECT id, amount, status, admin_note, created_at FROM payment_requests WHERE username = ? ORDER BY id DESC",
        conn, params=(username,)
    )
    conn.close()
    return df


def process_payment_request(request_id: int, action: str, admin_note: str = "") -> bool:
    """تایید یا رد درخواست شارژ کیف پول"""
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT username, amount, status FROM payment_requests WHERE id = ?", (request_id,))
    req = c.fetchone()
    if req:
        user, amount, current_status = req
        if current_status != "PENDING" and action == "APPROVED":
            conn.close()
            return False  # جلوگیری از شارژ مکرر درخواست‌های از قبل پردازش‌شده

        c.execute("UPDATE payment_requests SET status = ?, admin_note = ? WHERE id = ?",
                  (action, admin_note, request_id))
        if action == "APPROVED":
            c.execute("UPDATE users SET balance = balance + ? WHERE username = ?", (amount, user))
            # ثبت لاگ واریز
            c.execute("INSERT INTO logs (username, model, type, cost_toman) VALUES (?, ?, ?, ?)",
                      (user, "Wallet Deposit", "deposit", amount))

        conn.commit()
        conn.close()
        return True
    conn.close()
    return False


# ==========================================
# --- 4. BANK ACCOUNTS (حساب‌های بانکی) ---
# ==========================================
def add_bank_account(bank_name: str, owner_name: str, card_number: str, sheba_number: str = ""):
    """افزودن حساب بانکی جدید"""
    conn = get_connection()
    c = conn.cursor()
    c.execute("INSERT INTO bank_accounts (bank_name, owner_name, card_number, sheba_number) VALUES (?, ?, ?, ?)",
              (bank_name, owner_name, card_number, sheba_number))
    conn.commit()
    conn.close()


def delete_bank_account(account_id: int):
    """حذف یک حساب بانکی"""
    conn = get_connection()
    c = conn.cursor()
    c.execute("DELETE FROM bank_accounts WHERE id = ?", (account_id,))
    conn.commit()
    conn.close()


def get_bank_accounts() -> pd.DataFrame:
    """دریافت لیست حساب‌های بانکی سیستم"""
    conn = get_connection()
    df = pd.read_sql_query("SELECT * FROM bank_accounts", conn)
    conn.close()
    return df


# ==========================================
# --- 5. CHAT SESSIONS (جلسات چت) ---
# ==========================================
def create_new_session(username: str, first_message: str = "") -> str:
    """ایجاد یک سشن جدید برای چت"""
    username = username.strip().lower()
    session_id = str(uuid.uuid4())
    cleaned_title = first_message.strip().replace("\n", " ")
    title = (cleaned_title[:30] + "...") if len(cleaned_title) > 30 else (cleaned_title or "گفتگوی جدید")
    messages_json = json.dumps([])
    conn = get_connection()
    c = conn.cursor()
    c.execute("INSERT INTO sessions (session_id, username, title, messages) VALUES (?, ?, ?, ?)",
              (session_id, username, title, messages_json))
    conn.commit()
    conn.close()
    return session_id


def save_session_messages(session_id: str, messages: list):
    """ذخیره پیام‌های سشن در دیتابیس"""
    conn = get_connection()
    c = conn.cursor()
    messages_json = json.dumps(messages, ensure_ascii=False)
    c.execute("UPDATE sessions SET messages = ?, updated_at = CURRENT_TIMESTAMP WHERE session_id = ?",
              (messages_json, session_id))
    conn.commit()
    conn.close()


def rename_session(session_id: str, new_title: str) -> bool:
    """تغییر عنوان سشن گفتگو"""
    if not session_id or not new_title:
        return False
    conn = get_connection()
    c = conn.cursor()
    c.execute("UPDATE sessions SET title = ? WHERE session_id = ?", (new_title.strip(), session_id))
    conn.commit()
    conn.close()
    return True


def get_user_sessions(username: str) -> list:
    """دریافت سشن‌های کاربر به ترتیب آخرین بروزرسانی"""
    username = username.strip().lower()
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT session_id, title, updated_at FROM sessions WHERE username = ? ORDER BY updated_at DESC", (username,))
    rows = c.fetchall()
    conn.close()
    return rows


def load_session_messages(session_id: str) -> list:
    """بارگذاری لیست پیام‌های یک سشن"""
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT messages FROM sessions WHERE session_id = ?", (session_id,))
    row = c.fetchone()
    conn.close()
    if row and row[0]:
        try:
            return json.loads(row[0])
        except json.JSONDecodeError:
            return []
    return []


def delete_session(session_id: str):
    """حذف سشن گفتگو"""
    conn = get_connection()
    c = conn.cursor()
    c.execute("DELETE FROM sessions WHERE session_id = ?", (session_id,))
    conn.commit()
    conn.close()


# ==========================================
# --- 6. SYSTEM SETTINGS (تنظیمات سراسری) ---
# ==========================================
def get_setting(key: str, default: Any = None) -> Any:
    """خواندن مقدار یک تنظیم از پایگاه داده"""
    try:
        conn = get_connection()
        c = conn.cursor()
        c.execute("SELECT value FROM settings WHERE key = ?", (key,))
        row = c.fetchone()
        conn.close()
        if row is not None:
            return row[0]
    except Exception:
        pass
    return default


def set_setting(key: str, value: Any):
    """ذخیره یا بروزرسانی یک تنظیم در پایگاه داده"""
    conn = get_connection()
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, str(value)))
    conn.commit()
    conn.close()


def get_all_settings() -> Dict[str, str]:
    """دریافت کلیه تنظیمات ذخیره‌شده به صورت دیکشنری"""
    try:
        conn = get_connection()
        c = conn.cursor()
        c.execute("SELECT key, value FROM settings")
        rows = c.fetchall()
        conn.close()
        return {r[0]: r[1] for r in rows}
    except Exception:
        return {}


# ==========================================
# --- 7. IMAGE HISTORY (تاریخچه تصاویر) ---
# ==========================================
def save_image_history(username: str, prompt: str, image_url: str, model: str, cost: float):
    """ذخیره تصویر تولید شده در تاریخچه کاربر"""
    username = username.strip().lower()
    conn = get_connection()
    c = conn.cursor()
    c.execute("""INSERT INTO images_history (username, prompt, image_url, model, cost) 
                 VALUES (?, ?, ?, ?, ?)""",
              (username, prompt, image_url, model, float(cost)))
    conn.commit()
    conn.close()


def get_user_images_history(username: str, limit: int = 24) -> list:
    """دریافت تاریخچه تصاویر اخیر کاربر"""
    username = username.strip().lower()
    conn = get_connection()
    c = conn.cursor()
    c.execute("""SELECT id, prompt, image_url, model, cost, created_at 
                 FROM images_history 
                 WHERE username = ? 
                 ORDER BY id DESC LIMIT ?""", (username, limit))
    rows = c.fetchall()
    conn.close()
    return rows


# ==========================================
# --- 8. SYSTEM STATS (آمار تجمیعی سیستم) ---
# ==========================================
def get_system_stats() -> Dict[str, Any]:
    """محاسبه آمار کل سیستم برای داشبورد ادمین"""
    conn = get_connection()
    c = conn.cursor()

    c.execute("SELECT COUNT(*) FROM users")
    total_users = c.fetchone()[0]

    c.execute("SELECT SUM(cost_toman) FROM logs WHERE type != 'deposit'")
    total_revenue_row = c.fetchone()
    total_revenue = total_revenue_row[0] if total_revenue_row and total_revenue_row[0] else 0.0

    c.execute("SELECT COUNT(*) FROM payment_requests WHERE status = 'PENDING'")
    pending_payments = c.fetchone()[0]

    c.execute("SELECT COUNT(*) FROM sessions")
    total_sessions = c.fetchone()[0]

    c.execute("SELECT COUNT(*) FROM logs")
    total_requests = c.fetchone()[0]

    conn.close()
    return {
        "total_users": total_users,
        "total_revenue": total_revenue,
        "pending_payments": pending_payments,
        "total_sessions": total_sessions,
        "total_requests": total_requests
    }
