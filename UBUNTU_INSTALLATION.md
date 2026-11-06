# 🐧 راهنمای گام‌به‌گام نصب و راه‌اندازی AradGPT Pro 2.5 روی سرور اوبونتو (Ubuntu)
### **Ubuntu 20.04 / 22.04 / 24.04 LTS Server Production Deployment Guide**

این راهنما برای ادمین‌ها و مدیران سرور تهیه شده است تا بتوانند سامانه **AradGPT Pro 2.5** را از صفر تا صد روی یک سرور مجازی یا اختصاصی لینوکس اوبونتو (VPS / Dedicated Server) نصب، پیکربندی و با دامنه و HTTPS رایگان راه‌اندازی کنند.

---

## 📑 فهرست گام‌های نصب

1. [گام ۱: اتصال به سرور و بروزرسانی مخازن](#گام-۱-اتصال-به-سرور-و-بروزرسانی-مخازن)
2. [گام ۲: نصب پیش‌نیازهای سیستمی (پایتون، Nginx، Git)](#گام-۲-نصب-پیشنیازهای-سیستمی-پایتون-nginx-git)
3. [گام ۳: انتقال سورس کد به سرور](#گام-۳-انتقال-سورس-کد-به-سرور)
4. [گام ۴: ساخت محیط مجازی پایتون (venv) و نصب پکیج‌ها](#گام-۴-ساخت-محیط-مجازی-پایتون-venv-و-نصب-پکیجها)
5. [گام ۵: تنظیم فایل متغیرهای محیطی (.env)](#گام-۵-تنظیم-فایل-متغیرهای-محیطی-env)
6. [گام ۶: آماده‌سازی اولیه دیتابیس و کاتالوگ مدل‌ها](#گام-۶-آمادهسازی-اولیه-دیتابیس-و-کاتالوگ-مدلها)
7. [گام ۷: تنظیم سرویس همیشه‌روشن لینوکس (Systemd Service)](#گام-۷-تنظیم-سرویس-همیشهروشن-لینوکس-systemd-service)
8. [گام ۸: تنظیم وب‌سرور معکوس Nginx با بهینه‌سازی استریم SSE](#گام-۸-تنظیم-وبسرور-معکوس-nginx-با-بهینهسازی-استریم-sse)
9. [گام ۹: تنظیم فایروال سرور (UFW)](#گام-۹-تنظیم-فایروال-سرور-ufw)
10. [گام ۱۰: فعال‌سازی رایگان SSL و HTTPS با Certbot](#گام-۱۰-فعالسازی-رایگان-ssl-و-https-با-certbot)
11. [دستورات کاربردی مدیریت و نگهداری سرور](#دستورات-کاربردی-مدیریت-و-نگهداری-سرور)

---

## گام ۱: اتصال به سرور و بروزرسانی مخازن

ابتدا از طریق ترمینال (یا نرم‌افزار PuTTY) با دسترسی `root` به سرور خود متصل شوید:

```bash
ssh root@YOUR_SERVER_IP
```

مخازن نرم‌افزاری اوبونتو را به‌روزرسانی کنید:

```bash
sudo apt-get update && sudo apt-get upgrade -y
```

---

## گام ۲: نصب پیش‌نیازهای سیستمی (پایتون، Nginx، Git)

دستور زیر را برای نصب پایتون، مدیر بسته‌ها، وب‌سرور Nginx و ابزارهای ضروری وارد نمایید:

```bash
sudo apt-get install -y python3 python3-pip python3-venv git curl nginx ufw certbot python3-certbot-nginx
```

بررسی کنید که نسخه پایتون ۳.۱۰ یا بالاتر باشد:

```bash
python3 --version
```

---

## گام ۳: انتقال سورس کد به سرور

بهترین مسیر برای برنامه‌های سازمانی در لینوکس دایرکتوری `/opt` است. یک پوشه اختصاصی ایجاد کنید:

```bash
sudo mkdir -p /opt/aradgpt
cd /opt/aradgpt
```

اکنون سورس کدهای پروژه را از گیت‌هاب کلون کنید یا محتویات پروژه را در این پوشه قرار دهید:

```bash
# اگر از مخزن گیت کلون می‌کنید:
git clone https://github.com/YOUR_USERNAME/AI-AradGPT-Pro-main.git .

# یا اگر فایل‌های پروژه را به صورت دستی آپلود کرده‌اید، به همان مسیر بروید.
```

مجوزهای دسترسی پوشه را تنظیم کنید:

```bash
sudo chown -R $USER:$USER /opt/aradgpt
```

---

## گام ۴: ساخت محیط مجازی پایتون (venv) و نصب پکیج‌ها

برای جلوگیری از تداخل پکیج‌ها با پایتون سیستم‌عامل، یک محیط مجازی اختصاصی بسازید:

```bash
cd /opt/aradgpt
python3 -m venv venv
source venv/bin/activate
```

ارتقای ابزار `pip` و نصب کتابخانه‌های مورد نیاز از فایل `requirements.txt`:

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

---

## گام ۵: تنظیم فایل متغیرهای محیطی (`.env`)

فایل نمونه تنظیمات را کپی کرده و ویرایش کنید:

```bash
cp .env.example .env
nano .env
```

اطلاعات مورد نظر را در فایل وارد کنید (به ویژه کلید OpenRouter یا پرووایدر فعال):

```ini
ACTIVE_PROVIDER=openrouter
AI_API_KEY=sk-or-v1-YOUR_OPENROUTER_KEY_HERE
AI_BASE_URL=https://openrouter.ai/api/v1
USD_TO_TOMAN=85000
WELCOME_BONUS=20000
PORT=8501
HOST=0.0.0.0
```

برای ذخیره فایل در nano کلید `Ctrl+O` و سپس `Enter` را بزنید و با `Ctrl+X` خارج شوید.

---

## گام ۶: آماده‌سازی اولیه دیتابیس و کاتالوگ مدل‌ها

دستورات زیر را اجرا کنید تا پایگاه داده SQLite با مُد WAL ساخته شده و کاتالوگ ۴۵۵ مدل OpenRouter استخراج گردد:

```bash
python repair.py
python modules/parse_openrouter.py
```

---

## گام ۷: تنظیم سرویس همیشه‌روشن لینوکس (Systemd Service)

برای اینکه برنامه با بسته شدن ترمینال قطع نشود و در صورت ریستارت شدن سرور به طور خودکار بالا بیاید، یک سرویس Systemd می‌سازیم:

فایل سرویس را با ویرایشگر ایجاد کنید:

```bash
sudo nano /etc/systemd/system/aradgpt.service
```

محتوای زیر را درون آن قرار دهید:

```ini
[Unit]
Description=AradGPT Pro FastAPI Application Service
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/aradgpt
ExecStart=/opt/aradgpt/venv/bin/uvicorn main:app --host 127.0.0.1 --port 8501 --workers 2
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

فایل را ذخیره کرده (`Ctrl+O` و سپس `Ctrl+X`) و سرویس را فعال و استارت کنید:

```bash
sudo systemctl daemon-reload
sudo systemctl enable aradgpt
sudo systemctl start aradgpt
```

بررسی وضعیت سرویس (باید به رنگ سبز و `active (running)` باشد):

```bash
sudo systemctl status aradgpt
```

---

## گام ۸: تنظیم وب‌سرور معکوس Nginx با بهینه‌سازی استریم SSE

وب‌سرور Nginx درخواست‌های کاربران روی پورت ۸۰ و ۴۴۳ را دریافت کرده و به برنامه FastAPI هدایت می‌کند.

یک فایل کانفیگ برای سایت بسازید:

```bash
sudo nano /etc/nginx/sites-available/aradgpt
```

تنظیمات بهینه‌شده زیر را در آن قرار دهید:
*(توجه: عبارت `ai.yourdomain.com` را با دامنه واقعی خود جایگزین کنید)*

```nginx
server {
    listen 80;
    server_name ai.yourdomain.com;

    client_max_body_size 250M;

    access_log /var/log/nginx/aradgpt_access.log;
    error_log /var/log/nginx/aradgpt_error.log;

    gzip on;
    gzip_types text/plain text/css application/json application/javascript text/xml;

    location / {
        proxy_pass http://127.0.0.1:8501;
        proxy_http_version 1.1;

        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # تنظیمات حیاتی برای استریم کلمه به کلمه (Server-Sent Events)
        proxy_buffering off;
        proxy_cache off;
        proxy_set_header Connection '';
        chunked_transfer_encoding on;

        proxy_read_timeout 600s;
        proxy_send_timeout 600s;
        proxy_connect_timeout 60s;
    }

    location /static/ {
        proxy_pass http://127.0.0.1:8501/static/;
        expires 30d;
        add_header Cache-Control "public, no-transform";
    }

    location /assets/ {
        proxy_pass http://127.0.0.1:8501/assets/;
        expires 30d;
        add_header Cache-Control "public, no-transform";
    }
}
```

فایل را ذخیره کنید. اکنون کانفیگ را فعال کرده و Nginx را تست و ریستارت کنید:

```bash
sudo ln -sf /etc/nginx/sites-available/aradgpt /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl restart nginx
```

اگر خروجی `syntax is ok` و `test is successful` بود، Nginx به درستی پیکربندی شده است.

---

## گام ۹: تنظیم فایروال سرور (UFW)

برای امنیت سرور، پورت‌های لازم (SSH، HTTP و HTTPS) را باز کنید:

```bash
sudo ufw allow OpenSSH
sudo ufw allow 'Nginx Full'
sudo ufw enable
```

وضعیت فایروال را بررسی کنید:

```bash
sudo ufw status
```

---

## گام ۱۰: فعال‌سازی رایگان SSL و HTTPS با Certbot

برای فعال‌سازی پروتکل امن HTTPS و آیکون قفل سبز در مرورگر، با یک دستور گواهی رایگان Let's Encrypt بگیرید:

```bash
sudo certbot --nginx -d ai.yourdomain.com
```

- در پرسش اول ایمیل خود را وارد نمایید.
- در پرسش دوم قوانین را تایید کنید (`y`).
- در پاسخ به سوال ریدایرکت ترافیک، گزینه هدایت تمام ترافیک به HTTPS را برگزینید.

تمدید گواهی SSL به صورت اتوماتیک توسط Certbot انجام خواهد شد.

---

## 🎉 تبریک! سامانه آماده استفاده است

اکنون می‌توانید در مرورگر خود آدرس `https://ai.yourdomain.com` را باز کنید:

1. با اکانت پیش‌فرض مدیر ارشد وارد شوید:
   - **نام کاربری:** `admin`
   - **رمز عبور:** `admin123`
2. به بخش **کنترل‌پنل مدیریت ارشد > تب تنظیمات API** بروید و اتصال خود را تست کنید.
3. در تب **مدیریت کاربران**، کلمه عبور مدیر ارشد را تغییر دهید.

---

## 🔧 دستورات کاربردی مدیریت و نگهداری سرور

| عملیات | دستور در ترمینال سرور |
| :--- | :--- |
| **مشاهده وضعیت برنامه** | `sudo systemctl status aradgpt` |
| **ریستارت برنامه** | `sudo systemctl restart aradgpt` |
| **توقف برنامه** | `sudo systemctl stop aradgpt` |
| **مشاهده لاگ‌های زنده خطا و کارکرد** | `sudo journalctl -u aradgpt -f` |
| **بررسی وضعیت وب‌سرور Nginx** | `sudo systemctl status nginx` |
| **تست مجدد فایل کانفیگ Nginx** | `sudo nginx -t` |
| **ریستارت Nginx** | `sudo systemctl restart nginx` |
| **تهیه بکاپ فوری از دیتابیس و اسناد** | `tar -czvf /root/backup_$(date +%F).tar.gz /opt/aradgpt/data/` |
