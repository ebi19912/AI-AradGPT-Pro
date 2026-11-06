# modules/catalog.py
"""
سیستم کاتالوگ مدل‌های هوش مصنوعی با اعتبارسنجی خودکار شناسه‌ها و دسته‌بندی پیشرفته
حل قطعی مشکل 400 invalid model ID برای OpenRouter و یکپارچه‌سازی املای مدل‌ها
"""

import os
import json
import re
from typing import Dict, List, Any, Optional

VERIFIED_OPENROUTER_PATH = os.path.join("data", "openrouter_verified.json")

# دسته‌بندی‌های استاندارد و برچسب‌های فارسی
MODEL_CATEGORIES = {
    "recommended": {"name": "🌟 برگزیده و پیشنهادی", "badge": "پیشنهادی"},
    "free": {"name": "🎁 ۱۰۰٪ رایگان (Zero Cost)", "badge": "رایگان"},
    "reasoning": {"name": "🧠 تفکر عمیق و استدلال (Reasoning)", "badge": "استدلالی"},
    "coding": {"name": "💻 برنامه‌نویسی و توسعه (Coding)", "badge": "کدنویسی"},
    "flagship": {"name": "🚀 پرچمداران همه‌کاره (Flagship)", "badge": "پرچمدار"},
    "fast": {"name": "⚡ سریع و فوق اقتصادی", "badge": "سریع"},
    "image": {"name": "🎨 تولید تصویر و گرافیک", "badge": "تصویر"},
    "audio": {"name": "🎙️ صوت، گفتار و ویسپر", "badge": "صوت"},
    "embedding": {"name": "📚 مدل‌های امبدینگ و وکتور (Embedding)", "badge": "امبدینگ"}
}


def _load_verified_openrouter() -> List[Dict[str, Any]]:
    """بارگذاری مدل‌های معتبر OpenRouter"""
    if os.path.exists(VERIFIED_OPENROUTER_PATH):
        try:
            with open(VERIFIED_OPENROUTER_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass

    # در صورت عدم وجود، از فایل json قبلی یا لیست پیش‌فرض لود می‌کنیم
    old_json = os.path.join("data", "openrouter_models.json")
    if os.path.exists(old_json):
        try:
            with open(old_json, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass

    return []


_CACHED_OPENROUTER_MODELS = _load_verified_openrouter()


def normalize_model_id(provider_key: str, model_id: str) -> str:
    """
    اصلاح و نرمال‌سازی خودکار شناسه مدل بر اساس ارائه‌دهنده انتخابی
    برای جلوگیری از خطای ۴۰۰ 'not a valid model ID' در OpenRouter
    """
    if not model_id:
        return model_id

    provider_key = provider_key.lower().strip()
    if provider_key != "openrouter":
        return model_id

    global _CACHED_OPENROUTER_MODELS
    if not _CACHED_OPENROUTER_MODELS:
        _CACHED_OPENROUTER_MODELS = _load_verified_openrouter()

    # 1. تطابق دقیق
    if any(m["id"] == model_id for m in _CACHED_OPENROUTER_MODELS):
        return model_id

    # 2. بررسی پسوند :free
    free_variant = f"{model_id}:free"
    if any(m["id"] == free_variant for m in _CACHED_OPENROUTER_MODELS):
        return free_variant

    # 3. تطابق فازی خط تیره و فرمت (مثلاً dots3-note-preview -> dots-3-note-preview:free)
    clean_target = model_id.replace("-", "").replace("_", "").lower()
    for m in _CACHED_OPENROUTER_MODELS:
        clean_m = m["id"].replace("-", "").replace("_", "").replace(":free", "").lower()
        if clean_target == clean_m:
            return m["id"]

    for m in _CACHED_OPENROUTER_MODELS:
        clean_m = m["id"].replace("-", "").replace("_", "").replace(":free", "").lower()
        if clean_target in clean_m:
            return m["id"]

    return model_id


PROVIDER_CATALOGS: Dict[str, Dict[str, Any]] = {
    "openrouter": {
        "name": "OpenRouter",
        "description": "دسترسی آزاد به بیش از ۴۵۰ مدل جهانی با تفکیک دقیق مدل‌های رایگان و تجاری",
        "base_url": "https://openrouter.ai/api/v1",
        "models_loader": lambda: _CACHED_OPENROUTER_MODELS
    },
    "gapgpt": {
        "name": "GapGPT",
        "description": "پلتفرم متمرکز برای چت، تصویرسازی DALL-E/Flux و صوت Whisper",
        "base_url": "https://api.gapgpt.app/v1",
        "models": [
            # Chat Models
            {"id": "gpt-4o", "name": "GPT-4o (Omni)", "vendor": "openai", "category": "flagship", "description": "مدل چندمنظوره پرچمدار OpenAI", "context": "128K", "input_price": 2.5, "output_price": 10.0, "type": "chat"},
            {"id": "gpt-4o-mini", "name": "GPT-4o Mini", "vendor": "openai", "category": "fast", "description": "سریع، دقیق و اقتصادی برای پاسخگویی روزمره", "context": "128K", "input_price": 0.15, "output_price": 0.6, "type": "chat"},
            {"id": "o1-mini", "name": "OpenAI o1 Mini", "vendor": "openai", "category": "reasoning", "description": "مدل استدلال منطقی و ریاضی", "context": "128K", "input_price": 1.1, "output_price": 4.4, "type": "chat"},
            {"id": "o3-mini", "name": "OpenAI o3 Mini", "vendor": "openai", "category": "reasoning", "description": "استدلال پیشرفته پرسرعت", "context": "200K", "input_price": 1.1, "output_price": 4.4, "type": "chat"},
            {"id": "claude-3-7-sonnet-20250219", "name": "Claude 3.7 Sonnet", "vendor": "anthropic", "category": "coding", "description": "کلود ۳.۷ نسخه متفکر و برنامه‌نویس ارشد", "context": "200K", "input_price": 3.0, "output_price": 15.0, "type": "chat"},
            {"id": "deepseek-reasoner", "name": "DeepSeek R1 Reasoner", "vendor": "deepseek", "category": "reasoning", "description": "استدلال عمیق گام‌به‌گام دیپ‌سیک", "context": "64K", "input_price": 0.55, "output_price": 2.19, "type": "chat"},
            {"id": "deepseek-chat", "name": "DeepSeek V3 Chat", "vendor": "deepseek", "category": "fast", "description": "چت عمومی فوق ارزان و بسیار توانا", "context": "64K", "input_price": 0.14, "output_price": 0.28, "type": "chat"},
            {"id": "gemini-2.5-flash", "name": "Gemini 2.5 Flash", "vendor": "google", "category": "fast", "description": "مدل سریع گوگل با پنجره کانتکست عظیم", "context": "1M", "input_price": 0.15, "output_price": 0.6, "type": "chat"},
            # Image Models
            {"id": "gapgpt/flux.1-schnell", "name": "Flux.1 Schnell", "vendor": "black-forest-labs", "category": "image", "description": "تصویرسازی سریع و ارزان با فلوکس", "context": "1024x1024", "input_price": 0.003, "output_price": 0.003, "type": "image"},
            {"id": "gapgpt/flux.1-dev", "name": "Flux.1 Dev", "vendor": "black-forest-labs", "category": "image", "description": "کیفیت فوق‌العاده بالا و فوتورئال فلوکس", "context": "1024x1024", "input_price": 0.015, "output_price": 0.015, "type": "image"},
            {"id": "dall-e-3", "name": "DALL-E 3", "vendor": "openai", "category": "image", "description": "فهم استثنایی پرامپت و جزییات خیره‌کننده", "context": "1024x1024", "input_price": 0.04, "output_price": 0.04, "type": "image"},
            {"id": "dall-e-2", "name": "DALL-E 2", "vendor": "openai", "category": "image", "description": "مدل مناسب تغییر و واریانس عکس", "context": "1024x1024", "input_price": 0.02, "output_price": 0.02, "type": "image"},
            # Audio Models
            {"id": "tts-1", "name": "OpenAI TTS-1", "vendor": "openai", "category": "audio", "description": "تبدیل متن به گفتار روان و باکیفیت", "context": "audio/mp3", "input_price": 15.0, "output_price": 15.0, "type": "audio"},
            {"id": "tts-1-hd", "name": "OpenAI TTS-1 HD", "vendor": "openai", "category": "audio", "description": "کیفیت صدای استودیویی با وضوح بالا", "context": "audio/mp3", "input_price": 30.0, "output_price": 30.0, "type": "audio"},
            {"id": "gapgpt/whisper-1", "name": "Whisper-1 Transcribe", "vendor": "openai", "category": "audio", "description": "پیاده‌سازی صوت به متن با زبان فارسی", "context": "audio/transcription", "input_price": 10.0, "output_price": 10.0, "type": "audio"}
        ]
    },
    "openai": {
        "name": "OpenAI Official",
        "description": "سرورهای رسمی شرکت OpenAI",
        "base_url": "https://api.openai.com/v1",
        "models": [
            {"id": "gpt-4o", "name": "GPT-4o", "vendor": "openai", "category": "flagship", "description": "پرچمدار هوشمند OpenAI", "context": "128K", "input_price": 2.5, "output_price": 10.0, "type": "chat"},
            {"id": "gpt-4o-mini", "name": "GPT-4o Mini", "vendor": "openai", "category": "fast", "description": "سبک، دقیق و ارزان", "context": "128K", "input_price": 0.15, "output_price": 0.6, "type": "chat"},
            {"id": "o1", "name": "OpenAI o1", "vendor": "openai", "category": "reasoning", "description": "استدلال منطقی عمیق", "context": "200K", "input_price": 15.0, "output_price": 60.0, "type": "chat"},
            {"id": "o3-mini", "name": "OpenAI o3 Mini", "vendor": "openai", "category": "reasoning", "description": "استدلال سریع مسائل فنی", "context": "200K", "input_price": 1.1, "output_price": 4.4, "type": "chat"},
            {"id": "dall-e-3", "name": "DALL-E 3", "vendor": "openai", "category": "image", "description": "تولید تصویر با کیفیت بی‌نظیر", "context": "1024x1024", "input_price": 0.04, "output_price": 0.04, "type": "image"},
            {"id": "tts-1", "name": "OpenAI TTS", "vendor": "openai", "category": "audio", "description": "سنتز صدای طبیعی", "context": "audio", "input_price": 15.0, "output_price": 15.0, "type": "audio"},
            {"id": "whisper-1", "name": "OpenAI Whisper", "vendor": "openai", "category": "audio", "description": "تبدیل صوت به متن با ویسپر", "context": "stt", "input_price": 10.0, "output_price": 10.0, "type": "audio"}
        ]
    },
    "deepseek": {
        "name": "DeepSeek Official",
        "description": "سرویس مستقیم رسمی DeepSeek چین",
        "base_url": "https://api.deepseek.com/v1",
        "models": [
            {"id": "deepseek-chat", "name": "DeepSeek-V3", "vendor": "deepseek", "category": "fast", "description": "مدل چندمنظوره اقتصادی با فارسی‌نویسی عالی", "context": "64K", "input_price": 0.14, "output_price": 0.28, "type": "chat"},
            {"id": "deepseek-reasoner", "name": "DeepSeek-R1", "vendor": "deepseek", "category": "reasoning", "description": "استدلال گام‌به‌گام زنجیره افکار", "context": "64K", "input_price": 0.55, "output_price": 2.19, "type": "chat"}
        ]
    },
    "groq": {
        "name": "Groq Cloud",
        "description": "موتور پردازش LPU با سرعت ماورایی",
        "base_url": "https://api.groq.com/openai/v1",
        "models": [
            {"id": "deepseek-r1-distill-llama-70b", "name": "DeepSeek R1 Distill 70B", "vendor": "deepseek", "category": "reasoning", "description": "استدلال دیپ‌سیک روی زیرساخت لاما ۷۰B", "context": "128K", "input_price": 0.5, "output_price": 0.75, "type": "chat"},
            {"id": "llama-3.3-70b-versatile", "name": "Llama 3.3 70B Versatile", "vendor": "meta", "category": "flagship", "description": "پرچمدار متا با پاسخ‌دهی فوری", "context": "128K", "input_price": 0.35, "output_price": 0.4, "type": "chat"},
            {"id": "llama-3.1-8b-instant", "name": "Llama 3.1 8B Instant", "vendor": "meta", "category": "fast", "description": "پاسخ سریع با هزینه نزدیک به صفر", "context": "128K", "input_price": 0.05, "output_price": 0.08, "type": "chat"},
            {"id": "whisper-large-v3", "name": "Whisper Large V3 (Groq)", "vendor": "openai", "category": "audio", "description": "پیاده‌سازی صوت فوق سریع", "context": "audio/stt", "input_price": 5.0, "output_price": 5.0, "type": "audio"}
        ]
    },
    "custom": {
        "name": "سفارشی / محلی (Local / Ollama)",
        "description": "اتصال به سرورهای محلی یا سرور اختصاصی شما",
        "base_url": "http://localhost:11434/v1",
        "models": [
            {"id": "llama3.3", "name": "Local: Llama 3.3", "vendor": "local", "category": "fast", "description": "مدل محلی روی Ollama یا vLLM", "context": "32K", "input_price": 0.0, "output_price": 0.0, "type": "chat"},
            {"id": "deepseek-r1", "name": "Local: DeepSeek R1", "vendor": "local", "category": "reasoning", "description": "مدل استدلالی لوکال", "context": "32K", "input_price": 0.0, "output_price": 0.0, "type": "chat"}
        ]
    }
}


def get_all_providers() -> List[Dict[str, Any]]:
    result = []
    for key, data in PROVIDER_CATALOGS.items():
        result.append({
            "key": key,
            "name": data["name"],
            "description": data["description"],
            "base_url": data["base_url"]
        })
    return result


def get_models_for_provider(provider_key: str, model_type: Optional[str] = None) -> List[Dict[str, Any]]:
    provider_key = provider_key.lower().strip()
    catalog_entry = PROVIDER_CATALOGS.get(provider_key, PROVIDER_CATALOGS["openrouter"])

    if "models_loader" in catalog_entry:
        models = catalog_entry["models_loader"]()
    else:
        models = catalog_entry.get("models", [])

    if model_type:
        models = [m for m in models if m.get("type") == model_type]

    return models


def find_model_in_provider(provider_key: str, model_id: str) -> Optional[Dict[str, Any]]:
    normalized_id = normalize_model_id(provider_key, model_id)
    models = get_models_for_provider(provider_key)
    for m in models:
        if m["id"] == normalized_id or m["id"] == model_id:
            return m

    for m in models:
        if m["id"].endswith("/" + model_id) or model_id.endswith("/" + m["id"]):
            return m

    return None
