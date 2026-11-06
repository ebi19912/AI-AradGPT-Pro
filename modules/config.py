# modules/config.py
"""
ماژول مدیریت تنظیمات و پیکربندی سیستم AradGPT Pro
پشتیبانی کامل از ارائه‌دهنده‌های مختلف: OpenRouter, GapGPT, OpenAI, DeepSeek, Groq و Custom
بدون هیچ‌گونه وابستگی به Streamlit
"""

import os
from typing import Dict, Any, Optional

# بارگذاری متغیرهای محیطی از فایل .env در صورت وجود
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

DEFAULT_USD_TO_TOMAN = 85000
DEFAULT_WELCOME_BONUS = 20000  # ۲۰,۰۰۰ تومان هدیه ثبت‌نام
APP_VERSION = "2.0.0 Pro Enterprise"


def get_config_value(key: str, default: Any = None) -> Any:
    """
    دریافت یک تنظیم با اولویت:
    1. دیتابیس (جدول settings)
    2. متغیرهای محیطی (.env یا os.environ)
    3. کلیدهای معادل قدیمی
    4. مقدار پیش‌فرض
    """
    # 1. خواندن از پایگاه داده
    try:
        from modules.database import get_setting
        db_val = get_setting(key)
        if db_val is not None and str(db_val).strip() != "":
            return db_val
    except Exception:
        pass

    # 2. بررسی متغیرهای محیطی
    env_val = os.getenv(key)
    if env_val is not None and env_val.strip() != "":
        return env_val

    # کلیدهای معادل برای سازگاری عقب‌رو
    if key == "AI_API_KEY":
        for alt in ["OPENROUTER_API_KEY", "GAP_API_KEY", "OPENAI_API_KEY"]:
            alt_env = os.getenv(alt)
            if alt_env and alt_env.strip() != "":
                return alt_env

    return default


def set_config_value(key: str, value: Any):
    """ذخیره مقدار در دیتابیس برای دسترسی دائمی"""
    from modules.database import set_setting
    set_setting(key, str(value))


def get_active_provider_key() -> str:
    """دریافت کلید ارائه‌دهنده فعال (openrouter, gapgpt, openai, deepseek, groq, custom)"""
    prov = str(get_config_value("ACTIVE_PROVIDER", "openrouter")).lower().strip()
    return prov or "openrouter"


def get_active_base_url() -> str:
    """دریافت Base URL فعال"""
    custom_url = get_config_value("AI_BASE_URL")
    if custom_url:
        return custom_url.strip()

    from modules.catalog import PROVIDER_CATALOGS
    prov_key = get_active_provider_key()
    return PROVIDER_CATALOGS.get(prov_key, {}).get("base_url", "https://openrouter.ai/api/v1")


def get_active_api_key() -> str:
    """دریافت کلید API فعال"""
    key = get_config_value("AI_API_KEY", "")
    return str(key).strip() if key else ""


def get_usd_to_toman() -> int:
    """دریافت نرخ تبدیل دلار به تومان"""
    try:
        val = get_config_value("USD_TO_TOMAN", DEFAULT_USD_TO_TOMAN)
        return int(val)
    except Exception:
        return DEFAULT_USD_TO_TOMAN


def get_welcome_bonus() -> int:
    """دریافت مقدار هدیه ثبت‌نام برای کاربران جدید"""
    try:
        val = get_config_value("WELCOME_BONUS", DEFAULT_WELCOME_BONUS)
        return int(val)
    except Exception:
        return DEFAULT_WELCOME_BONUS
