# modules/pricing.py
"""
ماژول محاسبه قیمت و تعرفه مدل‌ها بر اساس ارائه‌دهنده فعال (Provider-Aware Pricing)
پشتیبانی از مدل‌های OpenRouter (بر اساس Openrouter.txt)، GapGPT، OpenAI، DeepSeek و مدل‌های سفارشی
"""

from typing import Dict, Any, Optional
from modules.config import get_usd_to_toman, get_active_provider_key
from modules.catalog import find_model_in_provider

# مقادیر پیش‌فرض تعرفه
DEFAULT_TEXT_PRICING = {"type": "text", "input_price": 1.00, "output_price": 3.00, "desc": "مدل عمومی استاندارد"}
DEFAULT_IMAGE_PRICING = {"type": "image", "input_price": 0.03, "output_price": 0.03, "desc": "مدل تصویرسازی عمومی"}
DEFAULT_AUDIO_PRICING = {"type": "audio", "input_price": 15.00, "output_price": 15.00, "desc": "مدل صوتی استاندارد"}


def get_model_info(model_name: str, provider: Optional[str] = None) -> Dict[str, Any]:
    """دریافت اطلاعات و تعرفه مدل از کاتالوگ ارائه‌دهنده فعال"""
    if not provider:
        provider = get_active_provider_key()

    found = find_model_in_provider(provider, model_name)
    if found:
        return found

    # جستجو در سایر ارائه‌دهنده‌ها در صورت لزوم
    for alt_prov in ["openrouter", "gapgpt", "openai", "deepseek", "groq"]:
        alt_found = find_model_in_provider(alt_prov, model_name)
        if alt_found:
            return alt_found

    fallback = dict(DEFAULT_TEXT_PRICING)
    fallback["name"] = model_name
    fallback["id"] = model_name
    fallback["description"] = f"مدل سفارشی ({model_name})"
    return fallback


def calculate_text_cost(model_name: str, input_tokens: int, output_tokens: int, provider: Optional[str] = None) -> float:
    """محاسبه دقیق هزینه مصرف توکن متن به تومان بر اساس نرخ روز ارز"""
    info = get_model_info(model_name, provider)
    usd_rate = get_usd_to_toman()

    in_price = info.get("input_price", 1.0)
    out_price = info.get("output_price", 3.0)

    # اگر مدل رایگان بود (Free)
    if info.get("is_free", False) or (in_price == 0.0 and out_price == 0.0):
        return 0.0

    cost_usd = ((input_tokens / 1_000_000) * in_price) + \
               ((output_tokens / 1_000_000) * out_price)

    # حداقل کارمزد هر درخواست متن: ۵ تومان
    cost_toman = max(5.0, cost_usd * usd_rate)
    return round(cost_toman, 2)


def calculate_image_cost(model_name: str, provider: Optional[str] = None) -> float:
    """محاسبه هزینه تولید یک عکس به تومان"""
    info = get_model_info(model_name, provider)
    usd_rate = get_usd_to_toman()

    if info.get("is_free", False):
        return 0.0

    price_usd = info.get("output_price") or info.get("input_price") or 0.03
    return max(50.0, round(price_usd * usd_rate, 0))


def calculate_audio_tts_cost(model_name: str, char_count: int, provider: Optional[str] = None) -> float:
    """محاسبه هزینه تبدیل متن به گفتار (TTS) به تومان"""
    info = get_model_info(model_name, provider)
    usd_rate = get_usd_to_toman()
    price_per_m = info.get("output_price") or info.get("input_price") or 15.0
    cost_usd = (char_count / 1_000_000) * price_per_m
    return max(50.0, round(cost_usd * usd_rate, 0))


def calculate_audio_stt_cost(model_name: str, text_length: int, provider: Optional[str] = None) -> float:
    """محاسبه هزینه پیاده‌سازی صوت به متن با ویسپر (STT) به تومان"""
    info = get_model_info(model_name, provider)
    usd_rate = get_usd_to_toman()
    price_per_m = info.get("output_price") or info.get("input_price") or 10.0
    cost_usd = (max(100, text_length) / 4 / 1_000_000) * price_per_m
    return max(50.0, round(cost_usd * usd_rate, 0))
