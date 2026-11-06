# modules/ai_client.py
"""
ماژول کلاینت هوش مصنوعی AradGPT Pro
مدیریت اتصالات به ارائه‌دهنده‌های مختلف بدون هیچ‌گونه وابستگی به Streamlit
"""

import time
from openai import OpenAI
from typing import Optional, Tuple, Dict, Any, List
from modules.config import (
    get_active_provider_key,
    get_active_base_url,
    get_active_api_key
)
from modules.catalog import PROVIDER_CATALOGS

_CLIENT_CACHE: Dict[str, OpenAI] = {}


def get_client() -> Optional[OpenAI]:
    """دریافت کلاینت فعال بر اساس آخرین تنظیمات سیستم"""
    api_key = get_active_api_key()
    base_url = get_active_base_url()

    if not api_key:
        return None

    cache_key = f"{base_url}::{api_key}"
    if cache_key in _CLIENT_CACHE:
        return _CLIENT_CACHE[cache_key]

    headers: Dict[str, str] = {}
    if "openrouter" in base_url.lower():
        headers["HTTP-Referer"] = "https://aradgpt.pro"
        headers["X-Title"] = "AradGPT Pro"

    try:
        client = OpenAI(
            api_key=api_key,
            base_url=base_url,
            default_headers=headers if headers else None,
            timeout=60.0
        )
        _CLIENT_CACHE[cache_key] = client
        return client
    except Exception as e:
        print(f"Error creating OpenAI client: {e}")
        return None


def clear_client_cache():
    """پاکسازی حافظه موقت کلاینت در زمان بروزرسانی تنظیمات"""
    global _CLIENT_CACHE
    _CLIENT_CACHE.clear()


def test_api_connection(api_key: str, base_url: str) -> Tuple[bool, str, float, List[str]]:
    """
    تست زنده اتصال به API ارائه‌دهنده انتخابی
    خروجی: (موفقیت: bool, پیام نتیجه: str, زمان پاسخ میلی‌ثانیه: float, لیست مدل‌ها: list)
    """
    if not api_key:
        return False, "کلید API وارد نشده است.", 0.0, []

    if not base_url:
        return False, "آدرس Base URL مشخص نشده است.", 0.0, []

    headers = {}
    if "openrouter" in base_url.lower():
        headers["HTTP-Referer"] = "https://aradgpt.pro"
        headers["X-Title"] = "AradGPT Pro"

    start_time = time.time()
    try:
        temp_client = OpenAI(
            api_key=api_key.strip(),
            base_url=base_url.strip(),
            default_headers=headers if headers else None,
            timeout=15.0
        )

        model_ids = []
        try:
            models_response = temp_client.models.list()
            if hasattr(models_response, "data"):
                model_ids = [m.id for m in models_response.data][:30]
        except Exception:
            pass

        if not model_ids:
            test_model = "gpt-4o-mini"
            if "deepseek" in base_url:
                test_model = "deepseek-chat"
            elif "groq" in base_url:
                test_model = "llama-3.1-8b-instant"
            elif "openrouter" in base_url:
                test_model = "openai/gpt-4o-mini"

            temp_client.chat.completions.create(
                model=test_model,
                messages=[{"role": "user", "content": "hi"}],
                max_tokens=2
            )

        latency = (time.time() - start_time) * 1000
        msg = f"اتصال به {base_url} با موفقیت برقرار شد. زمان پاسخ: {int(latency)}ms"
        if model_ids:
            msg += f" ({len(model_ids)} مدل شناسایی شد)"

        return True, msg, latency, model_ids

    except Exception as e:
        latency = (time.time() - start_time) * 1000
        err_msg = str(e)
        if "AuthenticationError" in err_msg or "401" in err_msg:
            return False, "خطای احراز هویت (401): کلید API نامعتبر است.", latency, []
        elif "NotFoundError" in err_msg or "404" in err_msg:
            return False, "خطای آدرس (404): آدرس Base URL اشتباه است یا مسیر /v1 وجود ندارد.", latency, []
        return False, f"خطا در برقراری ارتباط: {err_msg}", latency, []


def get_current_provider_info() -> Dict[str, Any]:
    """دریافت مشخصات کامل ارائه‌دهنده فعال"""
    prov_key = get_active_provider_key()
    prov_data = PROVIDER_CATALOGS.get(prov_key, PROVIDER_CATALOGS["openrouter"])
    base_url = get_active_base_url()
    api_key = get_active_api_key()

    masked_key = ""
    if api_key:
        if len(api_key) > 8:
            masked_key = f"{api_key[:4]}••••••••{api_key[-4:]}"
        else:
            masked_key = "••••••••"

    return {
        "key": prov_key,
        "name": prov_data.get("name", prov_key),
        "base_url": base_url,
        "api_key_masked": masked_key,
        "has_api_key": bool(api_key),
        "description": prov_data.get("description", "")
    }
