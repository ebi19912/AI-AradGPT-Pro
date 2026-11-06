# 🗄️ سند ۹: ساختار پایگاه داده و ذخیره‌سازی (Database Schema & Storage)
### **SQLite WAL Mode Engine, Tables Architecture & Vector Indexing**

---

## ۱. موتور پایگاه داده SQLite با مُد WAL
سامانه AradGPT Pro از پایگاه داده فایل‌محور **SQLite** در مسیر `data/gapgpt.db` بهره می‌برد.
برای تضمین کارکرد پرسرعت در محیط‌های چندکاربره و بارهای کاری سنگین وب‌سایت، در تابع `get_connection()` در ماژول [modules/database.py](file:///d:/AI-AradGPT-Pro-main/modules/database.py) دو تنظیم کلیدی اجرا می‌شود:

```python
conn = sqlite3.connect("data/gapgpt.db", timeout=30.0)
conn.execute("PRAGMA journal_mode=WAL;")
conn.execute("PRAGMA busy_timeout=30000;")
```
- **حالت WAL (Write-Ahead Logging):** به جای قفل کردن کل فایل دیتابیس در زمان نوشتن، تغییرات در یک فایل لاگ جانبی (`.db-wal`) ثبت شده و عملیات خواندن به هیچ وجه منتظر نوشتن نمی‌ماند.
- **تایم‌اوت ۳۰ ثانیه‌ای:** در صورت اوج ترافیک، پردازش‌ها به جای پرتاب خطای قفل شدن (`Database is locked`) تا ۳۰ ثانیه در صف منتظر اتمام تراکنش قبلی می‌مانند.

---

## ۲. دیاگرام ارتباطی جداول (Entity-Relationship Overview)

```
       ┌────────────────────────┐
       │         users          │
       ├────────────────────────┤
       │ username (PK)          │◄──────────┐
       │ password (SHA-256)     │           │
       │ balance (Float)        │           │
       │ role (user/admin)      │           │
       │ created_at             │           │
       └────────────────────────┘           │
         │          │          │            │
         ▼          ▼          ▼            │
┌──────────────┐ ┌────────┐ ┌────────────┐  │
│   deposits   │ │sessions│ │ usage_logs │  │
├──────────────┤ ├────────┤ ├────────────┤  │
│ id (PK)      │ │ id(PK) │ │ id (PK)    │  │
│ username(FK) │ │user(FK)│ │user(FK)    │  │
│ amount       │ │title   │ │model       │  │
│ status       │ │messages│ │type        │  │
└──────────────┘ └────────┘ └────────────┘  │
                                            │
┌────────────────────────┐                  │
│ knowledge_collections  │                  │
├────────────────────────┤                  │
│ id (UUID, PK)          │                  │
│ username (FK) ─────────┴──────────────────┘
│ title, desc, icon      │
└────────────────────────┘
         │
         ▼
┌────────────────────────┐
│  knowledge_documents   │
├────────────────────────┤
│ id (UUID, PK)          │
│ collection_id (FK)     │
│ title, chunk_count     │
└────────────────────────┘
         │
         ▼
┌────────────────────────┐
│    knowledge_chunks    │
├────────────────────────┤
│ id (UUID, PK)          │
│ document_id (FK)       │
│ collection_id (FK)     │
│ text (Snippet)         │
│ embedding (JSON vector)│
└────────────────────────┘
```

---

## ۳. تعریف دقیق فیلدهای جداول (Table Schemas)

### ۱. جدول کاربران (`users`)
```sql
CREATE TABLE users (
    username TEXT PRIMARY KEY,
    password TEXT NOT NULL,
    balance REAL DEFAULT 0.0,
    role TEXT DEFAULT 'user',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### ۲. جدول حساب‌های بانکی (`bank_accounts`)
```sql
CREATE TABLE bank_accounts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    bank_name TEXT NOT NULL,
    owner_name TEXT NOT NULL,
    card_number TEXT NOT NULL,
    sheba_number TEXT,
    is_active INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### ۳. جدول فیش‌های واریزی (`deposits`)
```sql
CREATE TABLE deposits (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL,
    amount REAL NOT NULL,
    receipt_image TEXT,
    status TEXT DEFAULT 'pending', -- pending, approved, rejected
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    reviewed_at TIMESTAMP,
    FOREIGN KEY(username) REFERENCES users(username)
);
```

### ۴. جدول سشن‌های چت (`sessions`)
```sql
CREATE TABLE sessions (
    session_id TEXT PRIMARY KEY,
    username TEXT NOT NULL,
    title TEXT,
    messages TEXT, -- آرایه پیام‌ها به فرمت JSON
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(username) REFERENCES users(username)
);
```

### ۵. جدول لاگ‌های مصرف (`usage_logs`)
```sql
CREATE TABLE usage_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL,
    model TEXT NOT NULL,
    type TEXT NOT NULL, -- chat, image, tts, stt
    cost_toman REAL NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(username) REFERENCES users(username)
);
```

### ۶. جدول مجموعه‌های پایگاه دانش (`knowledge_collections`)
```sql
CREATE TABLE knowledge_collections (
    id TEXT PRIMARY KEY,
    username TEXT NOT NULL,
    title TEXT NOT NULL,
    description TEXT,
    icon TEXT DEFAULT '📚',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(username) REFERENCES users(username)
);
```

### ۷. جدول اسناد پایگاه دانش (`knowledge_documents`)
```sql
CREATE TABLE knowledge_documents (
    id TEXT PRIMARY KEY,
    collection_id TEXT NOT NULL,
    username TEXT NOT NULL,
    title TEXT NOT NULL,
    char_count INTEGER DEFAULT 0,
    chunk_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(collection_id) REFERENCES knowledge_collections(id)
);
```

### ۸. جدول قطعات برداری پایگاه دانش (`knowledge_chunks`)
```sql
CREATE TABLE knowledge_chunks (
    id TEXT PRIMARY KEY,
    document_id TEXT NOT NULL,
    collection_id TEXT NOT NULL,
    text TEXT NOT NULL,
    chunk_index INTEGER DEFAULT 0,
    embedding TEXT NOT NULL, -- بردار وکتور به صورت JSON Array
    FOREIGN KEY(document_id) REFERENCES knowledge_documents(id),
    FOREIGN KEY(collection_id) REFERENCES knowledge_collections(id)
);
```

### ۹. جدول گالری تصاویر (`image_history`)
```sql
CREATE TABLE image_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL,
    prompt TEXT NOT NULL,
    image_url TEXT NOT NULL,
    model TEXT,
    style TEXT,
    size TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(username) REFERENCES users(username)
);
```

### ۱۰. جدول تنظیمات سیستم (`system_settings`)
```sql
CREATE TABLE system_settings (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);
```

---

## ۴. اسکریپت تعمیر و نگهداری دیتابیس (`repair.py`)
برای اطمینان از سلامت دیتابیس در زمان به‌روزرسانی نسخه‌ها، اسکریپت [repair.py](file:///d:/AI-AradGPT-Pro-main/repair.py) پیاده‌سازی شده است که:
1. وجود تمامی ستون‌های الزامی را چک کرده و در صورت نبود، آن‌ها را بدون حذف داده‌های قبلی ایجاد می‌کند (`ALTER TABLE ADD COLUMN`).
2. کاربر مدیر ارشد پیش‌فرض (`admin`) و تنظیمات اولیه را ثبت می‌نماید.
3. یکپارچگی ایندکس‌ها را بازرسی می‌کند.
