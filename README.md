# 🚀 AradGPT Pro 2.5 | سامانه جامع هوش مصنوعی چندرسانه‌ای و پایگاه دانش
### **Enterprise Multi-Provider AI Platform & Knowledge Studio (FastAPI Core)**

<div align="center">

![AradGPT Pro Logo](assets/logo.png)

### **پلتفرم جامع سازمانی: استودیو چت هوشمند، پایگاه دانش (RAG)، کاوشگر ۴۵۵ مدل، استودیو تصویر، پردازش صوت، کیف پول ریالی و کنترل‌پنل مدیریت ارشد**
**توسعه‌یافته بر پایه Pure FastAPI و معماری استاندارد مدرن وب (۱۰۰٪ مستقل از Streamlit)**
**با پشتیبانی از تمامی ارائه‌دهندگان: OpenRouter (۴۵۵ مدل احرازشده)، GapGPT، OpenAI، DeepSeek، Groq و Local LLMs**

[![Python Version](https://img.shields.io/badge/Python-3.10%2B-blue.svg?style=for-the-badge&logo=python)](https://python.org)
[![FastAPI Framework](https://img.shields.io/badge/FastAPI-0.110%2B-009688.svg?style=for-the-badge&logo=fastapi)](https://fastapi.tiangolo.com)
[![RAG Knowledge Engine](https://img.shields.io/badge/RAG%20Engine-Semantic%20Vectors-emerald.svg?style=for-the-badge)](#-پایگاه-دانش-هوشمند-سازمانی-rag)
[![Multi-Provider Support](https://img.shields.io/badge/AI%20Providers-OpenRouter%20%7C%20GapGPT%20%7C%20OpenAI%20%7C%20DeepSeek-8b5cf6.svg?style=for-the-badge)](https://openrouter.ai)
[![No Streamlit](https://img.shields.io/badge/Architecture-Pure%20FastAPI%20%2B%20SPA-success.svg?style=for-the-badge)](#)
[![Docker Ready](https://img.shields.io/badge/Docker-Ready-2496ED.svg?style=for-the-badge&logo=docker)](Dockerfile)

[🛠️ راهنمای جامع نصب و استقرار (INSTALLATION.md)](INSTALLATION.md) • [🐧 راهنمای اختصاصی نصب روی سرور اوبونتو (UBUNTU_INSTALLATION.md)](UBUNTU_INSTALLATION.md) • [📚 مستندات تفکیکی بخش‌ها (docs/)](#-مستندات-جامع-و-تفکیکی-پروژه-docs)

</div>

---

## 📑 فهرست مستندات جامع سامانه

تمام بخش‌ها، ماژول‌ها و ابزارهای سامانه به تفکیک در فایل‌های اختصاصی مستندسازی شده‌اند:

| سند | عنوان و موضوع | فایل مستند |
| :--- | :--- | :--- |
| **راهنمای نصب اوبونتو** | آموزش گام‌به‌گام و دستوری نصب روی سرور لینوکس Ubuntu با Nginx و SSL | [UBUNTU_INSTALLATION.md](UBUNTU_INSTALLATION.md) |
| **راهنمای نصب جامع** | راهنمای گام‌به‌گام نصب لینوکس، ویندوز، داکر، Nginx و SSL | [INSTALLATION.md](INSTALLATION.md) |
| **سند ۱** | معماری کلی سامانه، نمودار جریان داده و ساختار فایل‌ها | [docs/01-architecture.md](docs/01-architecture.md) |
| **سند ۲** | استودیو چت: استریم SSE، رندر مارک‌داون، استدلال و حافظه | [docs/02-chat-studio.md](docs/02-chat-studio.md) |
| **سند ۳** | پایگاه دانش سازمانی (RAG)، وکتورسازی و تشابه کسینوسی | [docs/03-knowledge-base-rag.md](docs/03-knowledge-base-rag.md) |
| **سند ۴** | کاوشگر مدل‌ها و کاتالوگ ۴۵۵ مدل OpenRouter و پرووایدرها | [docs/04-models-and-providers.md](docs/04-models-and-providers.md) |
| **سند ۵** | استودیو تصویر و گرافیک: تولید تصویر DALL-E و Flux و گالری | [docs/05-image-studio.md](docs/05-image-studio.md) |
| **سند ۶** | استودیو صوتی: تبدیل متن به گفتار (TTS) و Whisper (STT) | [docs/06-audio-studio.md](docs/06-audio-studio.md) |
| **سند ۷** | سیستم مالی، کیف پول، کارت‌های بانکی و تایید فیش | [docs/07-wallet-and-accounting.md](docs/07-wallet-and-accounting.md) |
| **سند ۸** | کنترل‌پنل مدیریت ارشد: آمار زنده، تنظیمات API و کاربران | [docs/08-admin-panel.md](docs/08-admin-panel.md) |
| **سند ۹** | ساختار پایگاه داده SQLite با مُد WAL و جداول سامانه | [docs/09-database-schema.md](docs/09-database-schema.md) |
| **سند ۱۰** | مرجع کامل اندپوینت‌های RESTful API و پی‌لودها | [docs/10-api-reference.md](docs/10-api-reference.md) |

---

## 🌟 قابلیت‌های کلیدی AradGPT Pro 2.5

1. **⚡ سرعت ماورایی با Pure FastAPI:** بدون کوچک‌ترین وابستگی به Streamlit؛ مصرف رم بسیار ناچیز و پردازش همزمان بالا.
2. **📝 رندرینگ استاندارد مارک‌داون (GFM):** تبدیل خودکار سرتیترهای `#` به عناوین استاندارد، ستاره‌های `*` به لیست‌های منظم و زیبای فارسی، جداول داده و بلوک‌های کد با دکمه کپی اختصاصی به همراه کتابخانه‌های محلی Marked.js و DOMPurify.
3. **🌓 موتور تم دوگانه (Dual Theme):** امکان سوئیچ میان تم تاریک نئونی و تم کریستالی روشن (Light Mode) تنها با یک کلیک.
4. **📚 پایگاه دانش سازمانی و شخصی (Semantic RAG):** آپلود فایل‌های PDF، Word، TXT، CSV و JSON؛ تقطیع هوشمند جملات فارسی، تولید بردار محلی و جستجوی شباهت کسینوسی و تزریق خودکار به چت.
5. **🔍 کاوشگر ۴۵۵ مدل OpenRouter:** دسترسی به تمامی مدل‌های روز دنیا (OpenAI, Anthropic, Google, DeepSeek, Meta, Mistral, Qwen) با مقایسه قیمت، پنجره کانتکست و فیلتر مدل‌های ۱۰۰٪ رایگان.
6. **🧠 تفکیک زنجیره تفکر و استدلال (Thinking):** نمایش مسیر استدلال مدل‌های پیشرفته نظیر DeepSeek-R1 به صورت کادر تاشو اختصاصی.
7. **🕒 مدیریت مکالمات و سشن‌های چت:** دکمه‌های برجسته چت جدید در نقاط کلیدی و پنجره جستجو و ویرایش تاریخچه گفتگوها.
8. **🎨 استودیو تصویرسازی چندموتوره:** تولید تصویر با DALL-E 3، Flux و Riverflow با ابعاد و استایل‌های هنری متنوع.
9. **🎙️ استودیو صوتی دوبعدی:** گویندگی هوشمند با ۶ لحن مختلف و پیاده‌سازی صوت به متن Whisper با ضبط مستقیم از میکروفون.
10. **💳 کیف پول ریالی و مدیریت کارت‌های بانکی:** ثبت فیش‌های واریزی، کارتابل تایید ادمین و کسر اتوماتیک هزینه از موجودی بر مبنای نرخ دلار روز.

---

## 🚀 راه‌اندازی سریع (Quick Start)

### با استفاده از Python و محیط مجازی:
```bash
# ۱. فعال‌سازی محیط مجازی و نصب پکیج‌ها
python -m venv venv
source venv/bin/activate  # در ویندوز: .\venv\Scripts\Activate.ps1
pip install -r requirements.txt

# ۲. ایجاد فایل تنظیمات
cp .env.example .env

# ۳. راه‌اندازی سرور
python -m uvicorn main:app --host 0.0.0.0 --port 8501
```

### با استفاده از Docker Compose:
```bash
docker compose up -d --build
```

- **آدرس دسترسی در مرورگر:** `http://localhost:8501`
- **حساب کاربری پیش‌فرض مدیر ارشد:** نام کاربری `admin` / رمز عبور `admin123`

برای آموزش‌های پیشرفته استقرار بر روی سرورهای Production، Nginx و SSL رایگان، لطفاً مستند [INSTALLATION.md](INSTALLATION.md) را مطالعه فرمایید.
