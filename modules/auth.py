# modules/auth.py
"""
ماژول احراز هویت و ثبت نام کاربران در سامانه AradGPT Pro
"""

import re
from typing import Optional, Tuple, Dict, Any
from modules.database import get_user, create_user, hash_password
from modules.config import get_welcome_bonus


def check_login(username: str, password: str) -> Optional[Dict[str, Any]]:
    """بررسی صحت نام کاربری و رمز عبور برای ورود"""
    if not username or not password:
        return None

    username = username.strip().lower()
    user = get_user(username)

    if user:
        stored_hash = user[1]
        input_hash = hash_password(password)

        if stored_hash == input_hash:
            return {
                "username": user[0],
                "balance": float(user[2]),
                "role": user[3],
                "created_at": user[4] if len(user) > 4 else None
            }

    return None


def register_user(username: str, password: str, confirm_password: str) -> Tuple[bool, Optional[Dict[str, Any]], str]:
    """
    ثبت نام کاربر جدید با اعتبارسنجی ورودی‌ها و اهدای شارژ هدیه خوش‌آمدگویی
    خروجی: (موفقیت: bool, اطلاعات کاربر: dict, پیام نتیجه: str)
    """
    username = username.strip().lower()

    if not username:
        return False, None, "لطفاً نام کاربری را وارد کنید."

    if len(username) < 3:
        return False, None, "نام کاربری باید حداقل ۳ کاراکتر باشد."

    if not re.match(r"^[a-zA-Z0-9_]+$", username):
        return False, None, "نام کاربری فقط می‌تواند شامل حروف انگلیسی، اعداد و خط تیره زیرین (_) باشد."

    if not password:
        return False, None, "لطفاً رمز عبور را وارد کنید."

    if len(password) < 6:
        return False, None, "رمز عبور باید حداقل ۶ کاراکتر باشد."

    if password != confirm_password:
        return False, None, "رمز عبور و تکرار آن یکسان نیستند."

    # بررسی عدم وجود کاربر قبلی
    existing = get_user(username)
    if existing:
        return False, None, "این نام کاربری قبلاً ثبت شده است. لطفاً نام دیگری انتخاب کنید."

    # اهدای موجودی اولیه هدیه
    initial_balance = float(get_welcome_bonus())

    created = create_user(username, password, balance=initial_balance, role="user")
    if created:
        user_info = {
            "username": username,
            "balance": initial_balance,
            "role": "user"
        }
        return True, user_info, f"حساب کاربری با موفقیت ساخته شد! {int(initial_balance):,} تومان هدیه خوش‌آمدگویی دریافت کردید."
    else:
        return False, None, "خطا در ایجاد حساب کاربری در پایگاه داده."
