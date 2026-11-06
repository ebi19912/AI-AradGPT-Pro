# 🌐 سند ۴: کاتالوگ مدل‌ها و مدیریت ارائه‌دهندگان (Multi-Provider Catalog)
### **Provider Aliasing, 455 OpenRouter Verified Models & Dynamic Pricing Engine**

---

## ۱. حل چالش تفاوت املا و شناسه‌های مدل‌ها (Provider Aliasing)
یکی از مشکلات بزرگ پلتفرم‌های هوش مصنوعی، تفاوت در نحوه نام‌گذاری مدل‌هاست:
- در **OpenRouter** شناسه مدل همراه با نام کمپانی است (مثلاً `openai/gpt-4o` یا `deepseek/deepseek-r1`).
- در **GapGPT** یا **OpenAI Official** همان مدل با شناسه ساده `gpt-4o` یا `deepseek-chat` فراخوانی می‌شود.
- در صورت ارسال یک شناسه با املای اشتباه به یک پرووایدر، خطای `400 Bad Request: model not found` رخ می‌دهد.

### راهکار پیاده‌سازی‌شده در `modules/catalog.py`:
سامانه با تابع هوشمند `normalize_model_id(provider_key, model_id)` به شکل خودکار شناسه مدل را متناسب با پرووایدر انتخابی نرمال‌سازی می‌کند:
```python
def normalize_model_id(provider_key: str, model_id: str) -> str:
    # اگر ارائه‌دهنده GapGPT یا OpenAI باشد و مدل حاوی پیشوند باشد، پیشوند حذف می‌شود
    # اگر ارائه‌دهنده OpenRouter باشد و پیشوند وجود نداشته باشد، نگاشت متناظر افزوده می‌شود
```

---

## ۲. کاتالوگ جامع ۴۵۵ مدل OpenRouter

تمامی مدل‌های استخراج‌شده از فایل مرجع `Openrouter.txt` اعتبارسنجی شده و در فایل [data/openrouter_verified.json](file:///d:/AI-AradGPT-Pro-main/data/openrouter_verified.json) ذخیره شده‌اند. این کاتالوگ شامل مشخصات کامل است:
- شناسه دقیق ارائه‌دهنده (Model ID)
- نام تجاری رسمی و کمپانی سازنده (Vendor)
- ظرفیت کانتکست (از 8K تا 1,000,000+ توکن)
- قیمت هر ۱ میلیون توکن ورودی به دلار
- قیمت هر ۱ میلیون توکن خروجی به دلار
- قیمت محاسبه‌شده لحظه‌ای به تومان
- دسته‌بندی کاربردی: `reasoning`, `coding`, `flagship`, `fast`, `free`, `image`

---

## ۳. ارائه‌دهندگان پشتیبانی‌شده در سامانه

| ارائه‌دهنده (Provider) | ویژگی‌ها و مزایا | Base URL پیش‌فرض |
| :--- | :--- | :--- |
| **OpenRouter** | دسترسی کامل به بیش از ۴۵۰ مدل دنیا، بهترین مدل‌های رایگان و تجاری | `https://openrouter.ai/api/v1` |
| **GapGPT** | سرویس چندرسانه‌ای داخلی با پشتیبانی از چت، تصویر و صوت | `https://api.gapgpt.app/v1` |
| **OpenAI Official** | سرویس رسمی شرکت OpenAI (مدل‌های GPT-4o, o1, DALL-E, Whisper, TTS) | `https://api.openai.com/v1` |
| **DeepSeek Official** | دسترسی ارزان و مستقیم به مدل‌های پرقدرت DeepSeek V3 و R1 | `https://api.deepseek.com/v1` |
| **Groq Cloud** | پردازش فوق‌سریع و آنی LPU (Llama 3.3, DeepSeek R1 Distill) | `https://api.groq.com/openai/v1` |
| **Custom / Ollama** | اتصال به مدل‌های محلی نصب‌شده روی سرور یا ارائه‌دهندگان دلخواه | `http://localhost:11434/v1` |

---

## ۴. پنل کاوشگر جامع مدل‌ها (Model Explorer)

این پنل در سایدبار اصلی با عنوان **🔍 کاوشگر مدل‌ها (۴۵۵)** تعبیه شده است:
1. **فیلترهای فوری برندها:** امکان تفکیک مدل‌ها تنها با یک کلیک بر اساس کمپانی:
   - 🟢 OpenAI
   - 🟠 Anthropic (خانواده Claude)
   - 🔵 Google (خانواده Gemini)
   - 🟣 DeepSeek (مدل‌های R1 و V3)
   - 🟦 Meta (خانواده Llama)
   - 🔴 Mistral AI
   - 🟡 Qwen (Alibaba)
   - 🎁 مدل‌های ۱۰۰٪ رایگان
2. **مرتب‌سازی هوشمند:** مرتب‌سازی بر اساس ارزان‌ترین مدل‌ها، گران‌ترین مدل‌ها، بزرگ‌ترین پنجره کانتکست یا حروف الفبا.
3. **دکمه انتخاب و شروع چت:** با زدن دکمه روی هر مدل، مدل مستقیماً در استودیو چت انتخاب و آماده گفتگو می‌شود.

---

## ۵. موتور محاسبه تعرفه و ریالی‌سازی (Pricing Engine)

در ماژول [modules/pricing.py](file:///d:/AI-AradGPT-Pro-main/modules/pricing.py):
1. نرخ برابری دلار به تومان از جدول تنظیمات پایگاه‌داده یا متغیر محیطی `USD_TO_TOMAN` استخراج می‌شود.
2. فرمول محاسبه هزینه هر درخواست:

$$Cost_{Toman} = \left( \frac{Tokens_{In}}{1,000,000} \times Price_{In}^{\$} + \frac{Tokens_{Out}}{1,000,000} \times Price_{Out}^{\$} \right) \times USD\_Rate$$

- مدل‌های رایگان (Free Models) به صورت خودکار با هزینه **۰ تومان** محاسبه شده و هیچ مبلغی از کاربر کسر نمی‌گردد.
- کاربر در هر لحظه در کنار نام مدل‌ها، تعرفه ورودی و خروجی به ازای هر ۱ میلیون توکن را به تومان مشاهده می‌نماید.
