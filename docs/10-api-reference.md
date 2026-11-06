# 📡 سند ۱۰: مرجع جامع اندپوینت‌های API (API Reference)
### **FastAPI RESTful Endpoints, Schemas, SSE Payloads & Status Codes**

---

## ۱. ساختار پایه‌ای ارتباط با API
- تمامی مسیرها با پیشوند `/api/` در دسترس هستند.
- فرمت تبادل داده‌ها در درخواست‌ها و پاسخ‌ها به صورت `application/json` است (به جز آپلود فایل‌ها که `multipart/form-data` است و استریم چت که `text/event-stream` است).
- احراز هویت از طریق کوکی امن `session_user` صورت می‌پذیرد.

---

## ۲. احراز هویت و حساب کاربری (Authentication)

### `GET /api/auth/me`
بررسی وضعیت ورود و دریافت پروفایل کاربر جاری.
- **پاسخ موفق (200 OK):**
```json
{
  "authenticated": true,
  "user": {
    "username": "admin",
    "balance": 50000.0,
    "role": "admin",
    "created_at": "2026-11-04 12:00:00"
  }
}
```

### `POST /api/auth/login`
ورود کاربر و ایجاد نشست.
- **بدنه درخواست:**
```json
{
  "username": "admin",
  "password": "admin123"
}
```
- **پاسخ موفق (200 OK):** ست شدن کوکی `session_user` و برگرداندن اطلاعات کاربر.

### `POST /api/auth/register`
ثبت‌نام کاربر جدید با اعمال خودکار شارژ هدیه خوش‌آمدگویی.
- **بدنه درخواست:**
```json
{
  "username": "new_user",
  "password": "password123"
}
```

### `POST /api/auth/logout`
خروج از حساب کاربری و باطل‌سازی کوکی نشست.

---

## ۳. ارائه‌دهنده‌ها و کاتالوگ مدل‌ها (Providers & Models)

### `GET /api/providers`
لیست تمامی ارائه‌دهندگان پیکربندی‌شده و نمایش ارائه‌دهنده فعال جاری.
- **پاسخ:**
```json
{
  "active_provider": "openrouter",
  "providers": [
    {"key": "openrouter", "name": "OpenRouter (تمامی مدل‌های دنیا - بیش از ۴۵۰ مدل)"},
    {"key": "gapgpt", "name": "GapGPT (سرویس چندرسانه‌ای داخلی)"},
    {"key": "openai", "name": "OpenAI Official (رسمی)"},
    {"key": "deepseek", "name": "DeepSeek Official (ارزان و توانا)"},
    {"key": "groq", "name": "Groq Cloud (فوق سریع LPU)"},
    {"key": "custom", "name": "سفارشی / محلی (Custom Base URL / Ollama)"}
  ]
}
```

### `GET /api/models?provider={provider_key}`
دریافت کاتالوگ کامل مدل‌های معتبر به همراه تعرفه ریالی و کانتکست.
- **پاسخ:**
```json
{
  "provider": "openrouter",
  "total": 455,
  "models": [
    {
      "id": "deepseek/deepseek-r1",
      "name": "DeepSeek R1",
      "vendor": "DeepSeek",
      "context": "164K",
      "input_price_toman": 468,
      "output_price_toman": 1862,
      "is_free": false,
      "category": "reasoning"
    }
  ]
}
```

---

## ۴. استودیو چت و استریم زنده (Chat Studio & Sessions)

### `POST /api/chat/stream`
استریم کلمه به کلمه پاسخ هوش مصنوعی به صورت Server-Sent Events (SSE).
- **بدنه درخواست (ChatStreamRequest):**
```json
{
  "session_id": "optional-uuid",
  "model": "deepseek/deepseek-r1",
  "messages": [
    {"role": "user", "content": "سلام، یک ایده تجاری برای من بنویس"}
  ],
  "system_prompt": "You are AradGPT Pro...",
  "temperature": 0.7,
  "knowledge_collection_id": "optional-collection-uuid"
}
```
- **فرمت استریم خروجی (`text/event-stream`):**
```text
data: {"reasoning": "در حال تفکر روی پرسش کاربر..."}

data: {"delta": "سلام"}

data: {"delta": "! حتماً، یک ایده جذاب:"}

data: {"done": true, "session_id": "6cd9b95d...", "new_balance": 48200.0}
```

### `POST /api/chat/extract-file`
استخراج آنی متن از فایل‌های ضمیمه‌شده به چت (PDF, Word, TXT, CSV, Code).
- **نوع ورودی:** `multipart/form-data` (فیلد `file`)
- **پاسخ:**
```json
{
  "filename": "document.pdf",
  "text": "محتوای استخراج‌شده از سند...",
  "token_estimate": 1420
}
```

### `GET /api/chat/sessions`
دریافت لیست سشن‌های گفتگوی اخیر کاربر جاری به ترتیب آخرین بروزرسانی.

### `PUT /api/chat/sessions/{session_id}`
تغییر عنوان سشن گفتگو (Rename Session).
- **بدنه درخواست:** `{"title": "عنوان جدید گفتگو"}`

### `DELETE /api/chat/sessions/{session_id}`
حذف سشن و تمامی پیام‌های متناظر با آن.

---

## ۵. پایگاه دانش و جستجوی معنایی (Knowledge Base & RAG)

### `GET /api/knowledge/collections`
لیست مجموعه‌های پایگاه دانش کاربر به همراه تعداد اسناد و قطعات برداری.

### `POST /api/knowledge/collections`
ساخت یک پایگاه دانش نو.
- **بدنه درخواست:**
```json
{
  "title": "آیین‌نامه‌های داخلی شرکت",
  "description": "دستورالعمل‌ها و ضوابط اداری سال ۱۴۰۳",
  "icon": "💼"
}
```

### `POST /api/knowledge/collections/{collection_id}/upload`
آپلود فایل سند خام به پایگاه دانش، استخراج خودکار متن، قطعه‌بندی هوشمند و تولید وکتور امبدینگ.
- **ورودی:** فایل Multipart (`.pdf`, `.docx`, `.txt`, `.csv`, `.json`, `.md`)

### `POST /api/knowledge/search`
انجام جستجوی معنایی بر مبنای تشابه کسینوسی بردارها (Vector Cosine Similarity).
- **بدنه درخواست:**
```json
{
  "collection_id": "uuid-here",
  "query": "شرایط مرخصی استعلاجی چیست؟",
  "top_k": 5
}
```
- **پاسخ:**
```json
{
  "results": [
    {
      "title": "آیین‌نامه مرخصی",
      "text": "ماده ۴: مرخصی استعلاجی با گواهی پزشک معتمد...",
      "score": 0.8942
    }
  ]
}
```

---

## ۶. استودیوهای تصویر و صوت (Image & Audio)

### `POST /api/image/generate`
تولید تصویر با موتورهای هوش مصنوعی.
- **بدنه درخواست:**
```json
{
  "model": "flux.1-schnell",
  "prompt": "یک شهر آینده‌نگرانه با نورپردازی بنفش و نئونی",
  "style": "photorealistic, 8k resolution",
  "size": "1024x1024"
}
```
- **پاسخ:** `{"success": true, "image_url": "/assets/generated/img_123.png"}`

### `POST /api/audio/tts`
تبدیل متن به فایل صوتی گفتار انسان (Text-to-Speech).
- **بدنه درخواست:**
```json
{
  "model": "tts-1",
  "text": "به سامانه AradGPT Pro خوش آمدید",
  "voice": "onyx",
  "speed": 1.0
}
```
- **خروجی:** فایل استریم با `media_type="audio/mpeg"`.

### `POST /api/audio/stt`
پیاده‌سازی فایل صوتی یا صدای ضبط‌شده با میکروفون به متن با Whisper (Speech-to-Text).
- **ورودی:** فایل صوتی Multipart و پارامتر زبان `language="fa"`.
- **پاسخ:** `{"text": "متن پیاده‌سازی‌شده با دقت کامل..."}`

---

## ۷. کیف پول و افزایش موجودی (Wallet)

### `GET /api/wallet/data`
دریافت اطلاعات کارت‌های بانکی فعال واریز وجه، سوابق فیش‌های کاربر و تاریخچه ریزتراکنش‌های مصرفی.

### `POST /api/wallet/deposit`
ثبت فیش واریزی کارت به کارت.
- **ورودی:** فیلد مبلغ (`amount: float`) و فایل تصویر فیش (`file: UploadFile`).

---

## ۸. کنترل‌پنل مدیریت ارشد (Admin APIs)

تمامی این اندپوینت‌ها نیازمند نقش `admin` هستند:
- `GET /api/admin/stats`: آمار کل کاربران، کل درآمد ریالی، فیش‌های منتظر و کل فراخوانی‌ها.
- `GET /api/admin/deposits`: دریافت لیست فیش‌های منتظر تایید.
- `POST /api/admin/deposits/{deposit_id}/review`: تایید (`action="approve"`) یا رد (`action="reject"`) فیش واریزی.
- `GET /api/admin/banks` و `POST /api/admin/banks`: مدیریت شماره کارت‌های بانکی مقصد.
- `GET /api/admin/users`: جستجو و فهرست کاربران.
- `POST /api/admin/users/{username}/balance`: تغییر شارژ کیف پول کاربر.
- `POST /api/admin/users/{username}/password`: تغییر رمز عبور کاربر.
- `POST /api/admin/users/{username}/role`: تغییر نقش به `user` یا `admin`.
- `DELETE /api/admin/users/{username}`: حذف کاربر.
- `GET /api/admin/settings` و `POST /api/admin/settings`: خواندن و ذخیره سراسری تنظیمات API.
- `POST /api/admin/test-api`: تست زنده اتصال و پینگ سرور ارائه‌دهنده.
- `GET /api/admin/logs`: دریافت گزارش لاگ‌های مصرف.
