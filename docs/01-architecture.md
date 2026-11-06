# 🏗️ سند ۱: معماری کلی سامانه و ساختار مهندسی نرم‌افزار
### **AradGPT Pro 2.5 System Architecture & Engineering Specifications**

---

## ۱. فلسفه طراحی و گذر از Streamlit به Pure FastAPI
سامانه **AradGPT Pro** در نسخه‌های اولیه از فریمورک Streamlit استفاده می‌کرد. با توجه به ماهیت Streamlit (اجرای مجدد کل اسکریپت در هر کنش کاربر، مصرف بالای رم، سشن‌های شکننده در وب‌سوکت و عدم امکان طراحی فرانت‌اند مدرن چندلایه‌ای)، در نسخه ۲.۵ معماری به صورت ۱۰۰٪ به **FastAPI + Modern Vanilla JS SPA** منتقل گردید:

```
+-----------------------------------------------------------------------------------------+
|                                    Client Browser                                       |
|  - Modern Vanilla JS SPA (app.js)                                                       |
|  - Dual Theme Engine (Light Mode / Cosmic Neon Dark Mode)                               |
|  - Marked.js (Offline GFM Parser) + DOMPurify (XSS Sanitizer)                            |
|  - Real-time Server-Sent Events (SSE) Reader & MediaRecorder API                         |
+-----------------------------------------------------------------------------------------+
                                           │
                               HTTP / SSE Streams
                                           │
                                           ▼
+-----------------------------------------------------------------------------------------+
|                                  FastAPI Core Gateway                                   |
|  - Asynchronous High-Concurrency ASGI Server (Uvicorn)                                  |
|  - Secure HTTPOnly Session Cookies & Role-Based Access Control (RBAC)                   |
|  - Document Text Extractors (PDF, DOCX, TXT, CSV, Code)                                 |
+-----------------------------------------------------------------------------------------+
         │                         │                               │
         ▼                         ▼                               ▼
+-----------------+      +--------------------+         +--------------------+
| SQLite Database |      | RAG Knowledge Base |         | Multi-Provider AI  |
| - WAL Mode      |      | - Sentence Chunker |         | - OpenRouter (455) |
| - Users & Auth  |      | - Hybrid N-Gram    |         | - GapGPT           |
| - Sessions      |      |   Vector Engine    |         | - OpenAI Official  |
| - Accounting    |      | - Cosine Sim Index |         | - DeepSeek Official|
| - Image History |      | - Document Store   |         | - Groq / Custom    |
+-----------------+      +--------------------+         +--------------------+
```

---

## ۲. مزایای معماری جدید
1. **استریم واقعی توکن‌ها (Real-Time SSE Streaming):** بدون وقفه و کلمه به کلمه، مشابه ChatGPT و Claude.
2. **پایداری ۱۰۰٪ همزمانی:** به کارگیری پایگاه داده SQLite در حالت `WAL (Write-Ahead Logging)` که مانع از قفل شدن دیتابیس در خواندن و نوشتن همزمان صدها کاربر می‌شود.
3. **صفر درصد وابستگی خارجی و شبکه (Zero CDN Dependency):** تمامی کتابخانه‌ها (قلم وزیرمتن، Marked.js، Purify.js، فونت‌ها و استایل‌ها) به صورت لوکال بر روی هاست قرار دارند و در شبکه‌های ایزوله یا اینترانت نیز بدون نقص کار می‌کنند.
4. **سیستم احراز هویت بدون وضعیت (Stateless Session Token via HTTPOnly Cookies):** ایمن در برابر حملات XSS و جعل هویت.

---

## ۳. ساختار دایرکتوری‌های پروژه

```
AI-AradGPT-Pro-main/
│
├── main.py                     # نقطه ورودی اصلی وب‌سرور FastAPI و تعریف تمام اندپوینت‌های REST
├── repair.py                   # اسکریپت اعتبارسنجی ساختار دیتابیس، جداول و ایندکس‌ها
├── requirements.txt            # پکیج‌های پایتون مورد نیاز پروژه
├── Dockerfile                  # تصویر استاندارد کانتینر داکر بر پایه python:3.11-slim
├── docker-compose.yml          # فایل ارکستریشن اجرای سرویس با حافظه ماندگار دیسک
├── deploy.sh                   # اسکریپت بش جهت نصب و راه‌اندازی خودکار در سرورهای اوبونتو
├── nginx.conf                  # نمونه تنظیمات Nginx Reverse Proxy با بهینه‌سازی اختصاصی SSE
├── aradgpt.service             # فایل سرویس systemd جهت اجرای پیوسته در پس‌زمینه لینوکس
│
├── modules/                    # ماژول‌های منطق برنامه (Business Logic)
│   ├── ai_client.py            # کلاینت واحد و کش‌شده برای ارتباط با OpenAI SDK و OpenRouter
│   ├── auth.py                 # اعتبارسنجی ورود، هشینگ گذرواژه (SHA-256) و مدیریت کوکی
│   ├── catalog.py              # نگاشت نام مدل‌ها، کاتالوگ ارائه‌دهندگان و مدیریت خطاها
│   ├── config.py               # خواندن متغیرهای محیطی از .env و مقادیر پیش‌فرض
│   ├── database.py             # مدیریت جداول SQLite، تراکنش‌ها، لاگ‌ها و سشن‌های چت
│   ├── knowledge.py            # موتور RAG: پایگاه دانش، تقطیع متن، وکتورسازی و سرچ معنایی
│   ├── parse_openrouter.py     # تجزیه‌گر کاتالوگ کامل مدل‌های OpenRouter و ذخیره در json
│   ├── pricing.py              # محاسبه تعرفه مدل‌ها بر اساس دلار روز و تبدیل به تومان
│   ├── ui.py                   # استایل‌ها و کامپوننت‌های کمکی
│   └── utils.py                # استخراج متن از فایلهای PDF، Word، TXT و تخمین توکن‌ها
│
├── templates/                  # تمپلیت‌های رابط کاربری
│   └── index.html              # صفحه اصلی SPA شامل تمامی پنل‌ها، مودال‌ها و تب‌های سامانه
│
├── static/                     # دارایی‌های استاتیک فرانت‌اند
│   ├── css/
│   │   └── style.css           # موتور استایل دوگانه (دارک نئونی و روشن)، گلس‌مورفیسم و تایپوگرافی
│   └── js/
│       ├── app.js              # کنترلر کلاینت SPA: سشن‌ها، استودیوها، ایونت‌ها و ارتباط با API
│       ├── marked.min.js       # موتور رندرینگ استانداردهای مارک‌داون GFM (آفلاین)
│       └── purify.min.js       # فیلتر امنیتی ضد تزریق کد (DOMPurify آفلاین)
│
├── data/                       # داده‌های ماندگار (توسط دیتابیس مدیریت می‌شوند)
│   ├── gapgpt.db               # پایگاه‌داده SQLite شامل تمام اطلاعات کاربران، تراکنش‌ها و اسناد
│   └── openrouter_verified.json# کاتالوگ احرازشده بیش از ۴۵۰ مدل هوش مصنوعی بین‌المللی
│
└── assets/                     # فایل‌های چندرسانه‌ای، لوگو و تصاویر خروجی کاربران
    ├── logo.svg                # لوگوی وکتور اختصاصی AradGPT
    └── logo.png                # لوگوی رستر سامانه
```
