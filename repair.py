# repair.py
import sqlite3
import hashlib
import os

# پیدا کردن مسیر دقیق پوشه فعلی
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_FOLDER = os.path.join(BASE_DIR, "data")
DB_PATH = os.path.join(DB_FOLDER, "gapgpt.db")

print(f"📂 مسیر دیتابیس: {DB_PATH}")

# ساخت پوشه اگر نباشد
if not os.path.exists(DB_FOLDER):
    os.makedirs(DB_FOLDER)
    print("✅ پوشه data ساخته شد.")

# اتصال به دیتابیس
conn = sqlite3.connect(DB_PATH)
c = conn.cursor()

# حذف جدول کاربران قدیمی (برای اطمینان)
try:
    c.execute("DROP TABLE IF EXISTS users")
    print("🗑️ جدول قدیمی کاربران پاک شد.")
except Exception as e:
    print(f"⚠️ خطا در حذف جدول: {e}")

# ساخت مجدد جدول
c.execute('''CREATE TABLE users (
                username TEXT PRIMARY KEY,
                password TEXT,
                balance REAL,
                role TEXT
            )''')

# ساخت رمز عبور (هش شده)
raw_pass = "admin123"
hashed_pass = hashlib.sha256(raw_pass.encode()).hexdigest()

print(f"🔑 رمز خام: {raw_pass}")
print(f"🔒 رمز هش شده برای ذخیره: {hashed_pass}")

# ایجاد کاربر ادمین
try:
    c.execute("INSERT INTO users VALUES (?, ?, ?, ?)", 
              ("admin", hashed_pass, 5000000.0, "admin"))
    conn.commit()
    print("✅ کاربر admin با موفقیت ساخته شد.")
except Exception as e:
    print(f"❌ خطا در ساخت کاربر: {e}")

# بررسی نهایی: آیا کاربر واقعاً در دیتابیس هست؟
c.execute("SELECT * FROM users WHERE username='admin'")
user = c.fetchone()
if user:
    print(f"🔎 تایید نهایی: کاربر {user[0]} در دیتابیس موجود است.")
else:
    print("❌ عجیب است! کاربر در دیتابیس پیدا نشد.")

conn.close()
print("🎉 تعمیر تمام شد. حالا app.py را اجرا کنید.")