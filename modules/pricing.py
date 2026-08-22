# modules/pricing.py
import os

# نرخ تبدیل دلار به تومان (قابل تغییر از فایل .env یا متغیرهای محیطی)
# پیش‌فرض: 80,000 تومان
USD_TO_TOMAN = int(os.getenv("USD_TO_TOMAN", 80000))

# مقادیر پیش‌فرض برای جلوگیری از ارور
DEFAULT_TEXT = {"type": "text", "input": 1.00, "output": 2.00, "desc": "مدل استاندارد"}

PRICING_DB = {
    # ==========================================
    # --- OPENAI: GPT-5 & GPT-4 SERIES ---
    # ==========================================
    "gpt-5": {"type": "text", "input": 1.25, "output": 10.00, "desc": "نسل جدید مدل‌های هوشمند OpenAI"},
    "gpt-5-mini": {"type": "text", "input": 0.25, "output": 2.00, "desc": "نسخه سبک و سریع GPT-5"},
    "gpt-5-nano": {"type": "text", "input": 0.05, "output": 0.40, "desc": "بسیار سبک و ارزان برای کارهای ساده"},
    "gpt-5.1": {"type": "text", "input": 1.25, "output": 10.00, "desc": "بهبود یافته GPT-5"},
    "gpt-5.2": {"type": "text", "input": 1.75, "output": 14.00, "desc": "نسخه پیشرفته‌تر با قابلیت‌های بیشتر"},
    "gpt-5.2-pro": {"type": "text", "input": 21.00, "output": 168.00, "desc": "قدرتمندترین و گران‌ترین نسخه حرفه‌ای"},
    "gpt-5-codex": {"type": "text", "input": 1.25, "output": 10.00, "desc": "تخصص در برنامه‌نویسی"},
    "gpt-5.1-codex": {"type": "text", "input": 1.25, "output": 10.00, "desc": "کدنویسی پیشرفته"},
    
    "gpt-4.5-preview": {"type": "text", "input": 75.00, "output": 150.00, "desc": "عظیم‌ترین مدل آزمایشی GPT-4"},
    "gpt-4o": {"type": "text", "input": 2.50, "output": 10.00, "desc": "هوشمندترین مدل چندمنظوره فعلی"},
    "gpt-4o-mini": {"type": "text", "input": 0.15, "output": 0.60, "desc": "اقتصادی‌ترین و سریع‌ترین مدل GPT-4"},
    "chatgpt-4o-latest": {"type": "text", "input": 5.00, "output": 15.00, "desc": "نسخه بهینه‌شده برای چت"},
    
    "gpt-4.1": {"type": "text", "input": 2.00, "output": 8.00, "desc": "نسخه بهبود یافته GPT-4"},
    "gpt-4.1-mini": {"type": "text", "input": 0.40, "output": 1.60, "desc": "نسخه کوچک GPT-4.1"},
    "gpt-4.1-nano": {"type": "text", "input": 0.10, "output": 0.40, "desc": "بسیار سریع و کم‌هزینه"},

    # ==========================================
    # --- OPENAI: O-SERIES (Reasoning) ---
    # ==========================================
    "o1": {"type": "text", "input": 15.00, "output": 60.00, "desc": "قدرتمندترین مدل استدلالی برای حل مسائل پیچیده"},
    "o1-mini": {"type": "text", "input": 1.10, "output": 4.40, "desc": "استدلال سریع و ارزان"},
    "o3": {"type": "text", "input": 2.00, "output": 8.00, "desc": "نسل سوم مدل‌های استدلالی"},
    "o3-mini": {"type": "text", "input": 1.10, "output": 4.40, "desc": "نسخه بهینه O3"},
    "o3-mini-high": {"type": "text", "input": 1.10, "output": 4.40, "desc": "O3 Mini با اولویت کیفیت"},
    "o3-mini-low": {"type": "text", "input": 1.10, "output": 4.40, "desc": "O3 Mini با اولویت سرعت"},
    "o4-mini": {"type": "text", "input": 1.10, "output": 4.40, "desc": "جدیدترین مدل استدلالی کوچک"},

    # ==========================================
    # --- XAI (Elon Musk - Grok) ---
    # ==========================================
    "grok-4": {"type": "text", "input": 3.00, "output": 15.00, "desc": "جدیدترین مدل XAI"},
    "grok-3": {"type": "text", "input": 3.00, "output": 15.00, "desc": "هوش مصنوعی قدرتمند Grok"},
    "grok-3-fast": {"type": "text", "input": 5.00, "output": 25.00, "desc": "Grok 3 با سرعت بالاتر"},
    "grok-3-mini": {"type": "text", "input": 0.30, "output": 1.50, "desc": "نسخه اقتصادی Grok"},
    "grok-3-mini-fast": {"type": "text", "input": 0.60, "output": 4.00, "desc": "سریع و سبک"},

    # ==========================================
    # --- GOOGLE (Gemini & Gemma) ---
    # ==========================================
    "gemini-3-pro-preview": {"type": "text", "input": 2.00, "output": 12.00, "desc": "پیش‌نمایش نسل سوم جمنای"},
    
    "gemini-2.5-pro": {"type": "text", "input": 2.50, "output": 20.00, "desc": "حرفه‌ای ترین مدل گوگل"},
    "gemini-2.5-flash": {"type": "text", "input": 0.30, "output": 2.50, "desc": "سریع و کارآمد"},
    "gemini-2.5-flash-lite": {"type": "text", "input": 0.10, "output": 0.40, "desc": "نسخه سبک Flash"},
    "gemini-live-2.5-flash-preview": {"type": "text", "input": 0.30, "output": 1.20, "desc": "مناسب مکالمات زنده"},
    
    # مدل‌های خاص و گران‌قیمت گوگل (Audio Thinking)
    "gemini-2.5-flash-exp-native-audio-thinking-dialog": {"type": "text", "input": 75.00, "output": 625.00, "desc": "گران‌قیمت: پردازش تفکر صوتی بومی"},
    "gemini-2.5-flash-preview-native-audio-dialog": {"type": "text", "input": 1.00, "output": 4.00, "desc": "پردازش صوتی"},

    "gemini-2.0-flash": {"type": "text", "input": 0.10, "output": 0.40, "desc": "مدل سریع و محبوب جمنای 2"},
    "gemini-2.0-flash-lite": {"type": "text", "input": 0.075, "output": 0.30, "desc": "ارزان‌ترین مدل فلش"},
    
    "gemma-3-27b-it": {"type": "text", "input": 0.013, "output": 0.050, "desc": "مدل متن‌باز گوگل (بسیار ارزان)"},

    # ==========================================
    # --- ANTHROPIC (Claude) ---
    # ==========================================
    "claude-3-7-sonnet-20250219": {"type": "text", "input": 3.00, "output": 15.00, "desc": "آخرین نسخه Sonnet با هوش بالا"},
    "claude-3-7-sonnet-20250219-thinking": {"type": "text", "input": 3.00, "output": 15.00, "desc": "نسخه متفکر Sonnet"},
    
    "claude-3-5-sonnet-20241022": {"type": "text", "input": 3.00, "output": 15.00, "desc": "محبوب‌ترین مدل برنامه‌نویسی"},
    "claude-3-5-haiku-20241022": {"type": "text", "input": 1.00, "output": 5.00, "desc": "سریع‌ترین مدل آنتروپیک"},
    
    "claude-sonnet-4-20250514": {"type": "text", "input": 3.00, "output": 15.00, "desc": "نسخه آینده Sonnet 4"},
    "claude-sonnet-4-5-20250929": {"type": "text", "input": 3.00, "output": 15.00, "desc": "نسخه آزمایشی Sonnet 4.5"},
    
    "claude-opus-4-1-20250805": {"type": "text", "input": 15.00, "output": 75.00, "desc": "قدرتمندترین مدل Opus"},
    "claude-opus-4-5-20251101": {"type": "text", "input": 3.00, "output": 15.00, "desc": "نسخه جدید Opus (قیمت تخمینی)"},

    # ==========================================
    # --- DEEPSEEK & ALIBABA (Qwen) ---
    # ==========================================
    "deepseek-reasoner": {"type": "text", "input": 0.55, "output": 0.55, "desc": "مدل استدلالی چینی (DeepSeek R1)"},
    "deepseek-chat": {"type": "text", "input": 0.27, "output": 0.27, "desc": "مدل چت عمومی V3"},
    
    "qwen3-coder-480b-a35b-instruct": {"type": "text", "input": 3.00, "output": 12.00, "desc": "مدل تخصصی کدنویسی Alibaba"},
    "qwen3-235b-a22b": {"type": "text", "input": 0.16, "output": 0.48, "desc": "مدل عمومی Qwen"},

    # ==========================================
    # --- IMAGE GENERATION (DALL-E, Flux, Imagen) ---
    # ==========================================
    "gapgpt/flux.1-schnell": {"type": "image", "price": 0.0014, "desc": "سریع‌ترین و ارزان‌ترین مدل تصویر"},
    "gapgpt/flux.1-dev": {"type": "image", "price": 0.014, "desc": "کیفیت بالای Flux"},
    
    "dall-e-3": {"type": "image", "price": 0.040, "desc": "بهترین فهم پرامپت (OpenAI)"},
    "dall-e-2": {"type": "image", "price": 0.018, "desc": "مدل کلاسیک OpenAI"},
    
    "gpt-image-1": {"type": "image", "price": 10.00, "desc": "مدل نسل جدید تصویر (گران)"},
    "gpt-image-1-mini": {"type": "image", "price": 2.00, "desc": "نسخه ارزان‌تر GPT Image"},
    
    "imagen-4.0-fast-generate-001": {"type": "image", "price": 0.020, "desc": "مدل سریع گوگل"},
    "imagen-4.0-ultra-generate-001": {"type": "image", "price": 0.060, "desc": "کیفیت Ultra گوگل"},
    
    "gemini-3-pro-image-preview": {"type": "image", "price": 2.00, "desc": "پیش‌نمایش تصویر جمنای 3"},
    "gemini-2.0-flash-preview-image-generation": {"type": "image", "price": 0.10, "desc": "تصویرسازی با جمنای 2"},

    # ==========================================
    # --- AUDIO (Text to Speech - TTS) ---
    # ==========================================
    "gpt-4o-mini-tts": {"type": "audio", "price": 0.60, "desc": "تبدیل متن به صدا (اقتصادی)"},
    "tts-1": {"type": "audio", "price": 15.00, "desc": "مدل استاندارد صدا"},
    "tts-1-hd": {"type": "audio", "price": 30.00, "desc": "کیفیت صدای HD"},
    
    "gemini-2.5-flash-preview-tts": {"type": "audio", "price": 0.50, "desc": "صدای گوگل Flash"},
    "gemini-2.5-pro-preview-tts": {"type": "audio", "price": 2.00, "desc": "صدای گوگل Pro"},

    # ==========================================
    # --- STT (Speech to Text) ---
    # ==========================================
    "gapgpt/whisper-1": {"type": "stt", "price": 30.00, "desc": "تبدیل صوت به متن (Whisper)"},
    "whisper-1": {"type": "stt", "price": 30.00, "desc": "نسخه اصلی OpenAI"},

    # ==========================================
    # --- EMBEDDINGS ---
    # ==========================================
    "text-embedding-3-small": {"type": "embedding", "input": 0.02, "output": 0.00, "desc": "امبدینگ سریع"},
    "text-embedding-3-large": {"type": "embedding", "input": 0.13, "output": 0.00, "desc": "امبدینگ دقیق"},
    "text-embedding-ada-002": {"type": "embedding", "input": 0.10, "output": 0.00, "desc": "امبدینگ لگاسی"},
}