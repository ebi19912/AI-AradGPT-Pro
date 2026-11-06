# 🛠️ راهنمای جامع نصب و استقرار سامانه AradGPT Pro 2.5
### **Enterprise Multi-Provider AI Platform Installation & Deployment Guide**

این مستند، راهنمای گام‌به‌گام و عملیاتی برای راه‌اندازی، نصب پیش‌نیازها و استقرار نسخه سازمانی پلتفرم **AradGPT Pro 2.5** بر روی سرورهای ابری، سرورهای لینوکس (Ubuntu / Debian / CentOS)، سرورهای ویندوز و همچنین محیط‌های داکر (Docker) است.

---

## 📑 فهرست مطالب
1. [پیش‌نیازهای سیستمی و سخت‌افزاری](#۱-پیشنیازهای-سیستمی-و-سختافزاری)
2. [تنظیم متغیرهای محیطی (.env)](#۲-تنظیم-متغیرهای-محیطی-env)
3. [روش اول: نصب دستی و مستقیم (پیشنهادی برای توسعه و سرور شخصی)](#۳-روش-اول-نصب-دستی-و-مستقیم)
4. [روش دوم: استقرار با Docker و Docker Compose (پیشنهادی برای Production)](#۴-روش-دوم-استقرار-با-docker-و-docker-compose)
5. [روش سوم: استقرار با اسکریپت خودکار deploy.sh](#۵-روش-سوم-استقرار-با-اسکریپت-خودکار-deploysh)
6. [تنظیم سرویس دائمی لینوکس (Systemd Service)](#۶-تنظیم-سرویس-دائمی-لینوکس-systemd-service)
7. [پیکربندی Nginx Reverse Proxy و بهینه‌سازی SSE](#۷-پیکربندی-nginx-reverse-proxy-و-بهینهسازی-sse)
8. [فعال‌سازی گواهی امنیتی SSL رایگان (Let's Encrypt)](#۸-فعالسازی-گواهی-امنیتی-ssl-رایگان-lets-encrypt)
9. [ورود اولیه مدیر ارشد و راه‌اندازی کلیدهای AI](#۹-ورود-اولیه-مدیر-ارشد-و-راهاندازی-کلیدهای-ai)
10. [پشتیبان‌گیری (Backup) و عیب‌یابی خطاهای رایج](#۱۰-پشتیبانگیری-و-عیبیابی-خطاهای-رایج)

---

## ۱. پیش‌نیازهای سیستمی و سخت‌افزاری

سامانه AradGPT Pro به دلیل استفاده مستقیم از فریمورک پرسرعت **FastAPI** و کلاینت وب سبک **Vanilla JS SPA**، بسیار بهینه بوده و نیازی به کارت گرافیک گران‌قیمت یا سرورهای سنگین ندارد (پردازش‌ها در سمت ارائه‌دهندگان هوش مصنوعی یا به صورت هیبرید انجام می‌گیرد):

| مشخصه | حداقل سیستم مورد نیاز (MVP) | سیستم پیشنهادی (سازمانی و پربار) |
| :--- | :--- | :--- |
| **سیستم‌عامل** | Ubuntu 22.04 LTS / Debian 12 / Windows 10+ | Ubuntu 24.04 LTS یا Debian 12 |
| **پردازنده (CPU)** | ۱ هسته | ۲ الی ۴ هسته |
| **حافظه رم (RAM)** | ۱ گیگابایت | ۲ الی ۴ گیگابایت |
| **فضای دیسک** | ۵ گیگابایت (SSD / NVMe) | ۲۰ گیگابایت به بالا (SSD) |
| **پایتون** | Python 3.10 تا 3.14 | Python 3.11 یا 3.12 |
| **پورت‌های آزاد** | `8501` (داخلی)، `80` و `443` (برای Nginx) | `8501`، `80` و `443` |

---

## ۲. تنظیم متغیرهای محیطی (`.env`)

پیش از اجرای برنامه، یک فایل با نام `.env` در ریشه اصلی پروژه ایجاد نمایید (می‌توانید از فایل نمونه `.env.example` کپی بگیرید):

```bash
cp .env.example .env
```

محتوای فایل `.env` را مطابق با تنظیمات خود ویرایش کنید:

```ini
# ==============================================================================
# پیکربندی ارائه‌دهنده فعال هوش مصنوعی (Active AI Provider)
# مقادیر مجاز: openrouter | gapgpt | openai | deepseek | groq | custom
# ==============================================================================
ACTIVE_PROVIDER=openrouter

# کلید دسترسی ارائه‌دهنده (برای OpenRouter کلید با sk-or-v1- آغاز می‌شود)
AI_API_KEY=sk-or-v1-your_openrouter_api_key_here

# آدرس پایه سرور ارائه‌دهنده
AI_BASE_URL=https://openrouter.ai/api/v1

# ==============================================================================
# پارامترهای مالی و حسابداری ریالی
# ==============================================================================
# نرخ تبدیل دلار به تومان (جهت محاسبه اتوماتیک هزینه مدل‌های بین‌المللی)
USD_TO_TOMAN=85000

# شارژ هدیه اولیه به کاربرانی که تازه ثبت‌نام می‌کنند (به تومان)
WELCOME_BONUS=20000

# ==============================================================================
# امنیت سشن و پورت اجرا
# ==============================================================================
SESSION_SECRET_KEY=aradgpt_secret_key_change_in_production_123456
PORT=8501
HOST=0.0.0.0
```

> **نکته مهم:** حتی اگر کلیدها را در `.env` وارد نکنید، مدیر ارشد می‌تواند در هر لحظه بدون ریستارت سرور، از داخل **کنترل‌پنل مدیریت ارشد > تب تنظیمات API** ارائه‌دهنده و کلید دسترسی را به صورت زنده تغییر دهد.

---

## ۳. روش اول: نصب دستی و مستقیم

### در محیط سرور لینوکس (Ubuntu / Debian):

#### گام ۱: بروزرسانی سیستم و نصب ابزارهای پایه
```bash
sudo apt-get update && sudo apt-get upgrade -y
sudo apt-get install -y python3 python3-pip python3-venv git curl
```

#### گام ۲: کلون کردن پروژه یا رفتن به مسیر آن
```bash
cd /opt/AI-AradGPT-Pro-main
# یا هر مسیری که کدها در آن قرار دارند
```

#### گام ۳: ایجاد محیط مجازی پایتون (venv) و فعال‌سازی آن
```bash
python3 -m venv venv
source venv/bin/activate
```

#### گام ۴: ارتقای pip و نصب پکیج‌های پیش‌نیاز
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

#### گام ۵: آماده‌سازی اولیه دیتابیس و کاتالوگ مدل‌ها
```bash
python repair.py
python modules/parse_openrouter.py
```

#### گام ۶: تست اجرای دستی برنامه
```bash
python -m uvicorn main:app --host 0.0.0.0 --port 8501
```
پس از مشاهده پیام `Application startup complete`، برنامه از طریق مرورگر در آدرس `http://YOUR_SERVER_IP:8501` در دسترس خواهد بود.

---

### در محیط ویندوز (Windows):

1. مطمئن شوید **Python 3.10+** بر روی ویندوز نصب است و گزینه `Add Python to PATH` تیک خورده باشد.
2. ترمینال PowerShell را در پوشه پروژه باز کنید:
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install --upgrade pip
pip install -r requirements.txt
python repair.py
python -m uvicorn main:app --host 0.0.0.0 --port 8501
```
3. مرورگر خود را باز کرده و به آدرس `http://localhost:8501` بروید.

---

## ۴. روش دوم: استقرار با Docker و Docker Compose

استفاده از داکر سریع‌ترین، استانداردترین و ایزوله‌ترین روش استقرار در محیط‌های Production است.

### پیش‌نیازها:
نصب بودن Docker و Docker Compose بر روی سرور:
```bash
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER
```

### اجرای پروژه با یک دستور:
در پوشه پروژه دستور زیر را وارد نمایید:

```bash
docker compose up -d --build
```

### بررسی وضعیت کانتینر:
```bash
docker compose ps
docker compose logs -f
```

کانتینر به صورت خودکار پورت `8501` را باز می‌کند و دیتابیس در پوشه `./data` بر روی هاست نگهداری می‌شود (Persistent Storage) تا هیچ اطلاعاتی با خاموش یا روشن شدن کانتینر حذف نگردد.

---

## ۵. روش سوم: استقرار با اسکریپت خودکار `deploy.sh`

برای استقرار فوق‌سریع در سرورهای اوبونتو، اسکریپت آماده [deploy.sh](file:///d:/AI-AradGPT-Pro-main/deploy.sh) تمام مراحل بالا را به صورت خودکار انجام می‌دهد:

```bash
chmod +x deploy.sh
./deploy.sh
```

این اسکریپت به شکل اتوماتیک:
1. پکیج‌های پایتون و لینوکس را نصب می‌کند.
2. محیط مجازی `venv` را ایجاد و پکیج‌ها را نصب می‌کند.
3. دیتابیس و مدل‌ها را بازسازی می‌کند.
4. فایل سرویس `aradgpt.service` را در Systemd تعریف و فعال می‌نماید.

---

## ۶. تنظیم سرویس دائمی لینوکس (Systemd Service)

برای اطمینان از اینکه برنامه همواره در پس‌زمینه اجرا باشد و با ریستارت شدن سرور به طور خودکار بالا بیاید:

### ۱. ایجاد فایل سرویس
فایل `/etc/systemd/system/aradgpt.service` را با ویرایشگر باز کنید:
```bash
sudo nano /etc/systemd/system/aradgpt.service
```

### ۲. درج پیکربندی سرویس:
```ini
[Unit]
Description=AradGPT Pro Enterprise AI Engine
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/AI-AradGPT-Pro-main
ExecStart=/opt/AI-AradGPT-Pro-main/venv/bin/uvicorn main:app --host 0.0.0.0 --port 8501 --workers 2
Restart=always
RestartSec=3
StandardOutput=journal
StandardError=journal
Environment=PYTHONUNBUFFERED=1
Environment=LC_ALL=C.UTF-8
Environment=LANG=C.UTF-8

[Install]
WantedBy=multi-user.target
```
*(مسیرها را مطابق با محل قرارگیری پروژه خود در سرور تنظیم فرمایید)*

### ۳. راه‌اندازی و فعال‌سازی سرویس:
```bash
sudo systemctl daemon-reload
sudo systemctl enable aradgpt
sudo systemctl start aradgpt
```

### ۴. بررسی وضعیت کارکرد:
```bash
sudo systemctl status aradgpt
```

---

## ۷. پیکربندی Nginx Reverse Proxy و بهینه‌سازی SSE

برای دسترسی کاربران از طریق دامنه (مثلاً `ai.yourcompany.com`) به پورت‌های استاندارد `80` و `443` و فعال‌سازی پروتکل Server-Sent Events بدون وقفه:

### ۱. کپی فایل کانفیگ Nginx
فایل آماده [nginx.conf](file:///d:/AI-AradGPT-Pro-main/nginx.conf) را در مسیر تنظیمات وب‌سرور قرار دهید:
```bash
sudo cp nginx.conf /etc/nginx/sites-available/aradgpt
sudo nano /etc/nginx/sites-available/aradgpt
```
نام دامنه خود را در جلوی `server_name` وارد نمایید:
```nginx
server_name ai.yourcompany.com;
```

### ۲. فعال‌سازی تنظیمات در Nginx
```bash
sudo ln -sf /etc/nginx/sites-available/aradgpt /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl restart nginx
```

> **پارامتر کلیدی استریم:** در فایل `nginx.conf` خط `proxy_buffering off;` قرار دارد. این دستور از بافر شدن استریم هوش مصنوعی در Nginx جلوگیری کرده و باعث می‌شود پاسخ مدل‌ها بلافاصله و کلمه به کلمه (تایپینگ زنده) به مرورگر کاربر ارسال شود.

---

## ۸. فعال‌سازی گواهی امنیتی SSL رایگان (Let's Encrypt)

برای اینکه ارتباط کاربران با پروتکل امن `https://` و قفل سبز مرورگر برقرار شود:

```bash
sudo apt-get install -y certbot python3-certbot-nginx
sudo certbot --nginx -d ai.yourcompany.com
```
در مراحل نصب، ایمیل خود را وارد کرده و در پاسخ به پرسش هدایت ترافیک، گزینه `Redirect (2)` را انتخاب کنید تا تمامی درخواست‌های `http` به صورت خودکار به `https` منتقل شوند.

---

## ۹. ورود اولیه مدیر ارشد و راه‌اندازی کلیدهای AI

پس از باز کردن سامانه در مرورگر:
1. روی تب **🔑 ورود به حساب** کلیک کنید.
2. با مشخصات مدیر ارشد پیش‌فرض وارد شوید:
   - **نام کاربری:** `admin`
   - **رمز عبور پیش‌فرض:** `admin123`
3. در سایدبار راست، منوی **⚙️ کنترل‌پنل مدیریت ارشد** نمایان خواهد شد.
4. به تب **🔌 تنظیمات API و سیستم** بروید:
   - پرووایدر مورد نظر خود را انتخاب کنید (مثلاً OpenRouter).
   - کلید API خود (`sk-or-v1-...`) را وارد نمایید.
   - دکمه **⚡ تست زنده اتصال به API** را بزنید تا از برقراری ارتباط و پینگ سرور مطمئن شوید.
   - دکمه **💾 ذخیره تنظیمات** را بزنید تا کلید به صورت سراسری فعال شود.
5. به تب **👥 مدیریت کاربران** بروید و رمز عبور حساب `admin` را تغییر دهید.

---

## ۱۰. پشتیبان‌گیری و عیب‌یابی خطاهای رایج

### تهیه بکاپ از اطلاعات (Backup):
تمام کاربران، تاریخچه چت‌ها، وکتورهای پایگاه دانش و فیش‌ها در پوشه `data/` ذخیره می‌شوند. برای پشتیبان‌گیری کافیست این پوشه را فشرده و نگهداری کنید:
```bash
tar -czvf backup_aradgpt_$(date +%Y%m%d).tar.gz data/
```

### عیب‌یابی (Troubleshooting):

1. **خطای `Database Locked` در SQLite:**
   - پایگاه‌داده AradGPT از مُد مدرن `WAL (Write-Ahead Logging)` بهره می‌برد و این خطا حل شده است. در صورت بروز هرگونه مشکل ناشی از دسترسی دیسک در سرورهای اشتراکی:
   ```bash
   python repair.py
   ```

2. **قطع شدن یا بافر شدن استریم چت در پشت Nginx:**
   - مطمئن شوید در فایل کانفیگ Nginx خطوط زیر وجود داشته باشد:
   ```nginx
   proxy_buffering off;
   proxy_cache off;
   chunked_transfer_encoding on;
   ```

3. **خطای `Error code: 401 Unauthorized` از هوش مصنوعی:**
   - کلید API وارد شده منقضی یا اشتباه است یا موجودی دلاری آن کافی نیست. به پنل ادمین رفته و با دکمه تست پینگ، کلید را اعتبارسنجی فرمایید.

4. **مشاهده لاگ‌های زنده سرویس در لینوکس:**
   ```bash
   sudo journalctl -u aradgpt -f
   ```
