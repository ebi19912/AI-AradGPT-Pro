# repair.py
"""
ابزار عیب‌یابی، راه‌اندازی و تعمیر دیتابیس AradGPT Pro
این اسکریپت ساختار پایگاه‌داده را بررسی، بروزرسانی و کاربر ادمین پیش‌فرض را ایجاد می‌کند.
"""

import sqlite3
import hashlib
import os
import sys

# تنظیم انکودینگ خروجی ترمینال به UTF-8 برای جلوگیری از خطای یونیکد در ویندوز
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding='utf-8')

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_FOLDER = os.path.join(BASE_DIR, "data")
DB_PATH = os.path.join(DB_FOLDER, "gapgpt.db")

print("=" * 60)
print("🛠️ ابزار بررسی و تعمیر پایگاه داده سامانه AradGPT Pro")
print("=" * 60)
print(f"📂 مسیر دیتابیس: {DB_PATH}")

if not os.path.exists(DB_FOLDER):
    os.makedirs(DB_FOLDER)
    print("✅ پوشه data ایجاد گردید.")

# اتصال به دیتابیس
conn = sqlite3.connect(DB_PATH)
c = conn.cursor()

# فعال‌سازی WAL mode
c.execute("PRAGMA journal_mode=WAL;")

# 1. جدول کاربران
c.execute('''CREATE TABLE IF NOT EXISTS users (
                username TEXT PRIMARY KEY,
                password TEXT,
                balance REAL DEFAULT 0,
                role TEXT DEFAULT 'user',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )''')
print("✅ جدول users بررسی و تایید شد.")

# 2. جدول لاگ‌ها
c.execute('''CREATE TABLE IF NOT EXISTS logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT,
                model TEXT,
                type TEXT,
                cost_toman REAL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )''')
print("✅ جدول logs بررسی و تایید شد.")

# 3. جدول درخواست‌های شارژ
c.execute('''CREATE TABLE IF NOT EXISTS payment_requests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT,
                amount INTEGER,
                receipt_img BLOB,
                status TEXT DEFAULT "PENDING",
                admin_note TEXT DEFAULT "",
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )''')
print("✅ جدول payment_requests بررسی و تایید شد.")

# 4. جدول حساب‌های بانکی
c.execute('''CREATE TABLE IF NOT EXISTS bank_accounts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                bank_name TEXT,
                owner_name TEXT,
                card_number TEXT,
                sheba_number TEXT
            )''')
print("✅ جدول bank_accounts بررسی و تایید شد.")

# 5. جدول سشن‌ها
c.execute('''CREATE TABLE IF NOT EXISTS sessions (
                session_id TEXT PRIMARY KEY,
                username TEXT,
                title TEXT,
                messages TEXT,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )''')
print("✅ جدول sessions بررسی و تایید شد.")

# 6. جدول تنظیمات
c.execute('''CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT
            )''')
print("✅ جدول settings بررسی و تایید شد.")

# 7. جدول تاریخچه تصاویر
c.execute('''CREATE TABLE IF NOT EXISTS images_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT,
                prompt TEXT,
                image_url TEXT,
                model TEXT,
                cost REAL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )''')
print("✅ جدول images_history بررسی و تایید شد.")

# تنظیم مقادیر اولیه
default_settings = {
    "ACTIVE_PROVIDER": "openrouter",
    "USD_TO_TOMAN": "85000",
    "WELCOME_BONUS": "20000",
    "APP_TITLE": "AradGPT Pro",
    "ENABLE_REGISTRATION": "true"
}
for k, v in default_settings.items():
    c.execute("INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)", (k, v))

# بررسی و ایجاد حساب کاربری ادمین
c.execute("SELECT * FROM users WHERE username='admin'")
admin_user = c.fetchone()
if not admin_user:
    hashed_pw = hashlib.sha256("admin123".encode()).hexdigest()
    c.execute("INSERT INTO users (username, password, balance, role) VALUES (?, ?, ?, ?)",
              ("admin", hashed_pw, 5000000.0, "admin"))
    print("✨ کاربر ادمین جدید ایجاد شد: نام کاربری: admin | رمز عبور: admin123")
else:
    print(f"👤 کاربر ادمین از قبل در دیتابیس وجود دارد: {admin_user[0]} (موجودی: {admin_user[2]:,} تومان)")

conn.commit()
conn.close()

print("=" * 60)
print("🎉 عملیات بررسی و راه‌اندازی با موفقیت انجام شد!")
print("🚀 برای اجرای برنامه دستور زیر را در ترمینال بزنید:")
print("   streamlit run app.py")
print("=" * 60)
