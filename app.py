# app.py
import os
import streamlit as st
from openai import OpenAI

# ماژول‌های داخلی
from modules.auth import check_login
from modules.database import (
    init_db, 
    get_user, 
    get_user_sessions, 
    delete_session, 
    load_session_messages
)
# اضافه کردن تابع جدید به ایمپورت ui
from modules.ui import setup_page_config, inject_floating_action_buttons

# صفحات
from views import chat, image, audio, wallet, admin

# ==========================================
# 1. تنظیمات و راه‌اندازی (SETUP)
# ==========================================
LOGO_PATH = os.path.join("assets", "logo.png")
PAGE_ICON = LOGO_PATH if os.path.exists(LOGO_PATH) else "🤖"

# اعمال تنظیمات UI پیشرفته (Qwen Theme)
setup_page_config(PAGE_ICON)
init_db()

# ==========================================
# 2. کلاینت و سشن (CLIENT & SESSION)
# ==========================================
if "user" not in st.session_state:
    st.session_state.user = None

def get_client():
    try:
        api_key = st.secrets.get("GAP_API_KEY")
        if api_key:
            return OpenAI(api_key=api_key, base_url="https://api.gapgpt.app/v1")
    except Exception:
        pass
    return None

client = get_client()

# ==========================================
# 3. لاجیک اصلی (MAIN LOGIC)
# ==========================================
def main():
    if not st.session_state.user:
        render_login()
    else:
        render_dashboard()

def render_login():
    """صفحه ورود مینیمال با افکت شیشه‌ای"""
    col1, col2, col3 = st.columns([1, 1.2, 1])
    with col2:
        # استفاده از کارت شیشه‌ای برای فرم ورود
        st.markdown('<div class="modern-card" style="text-align:center;">', unsafe_allow_html=True)
        st.markdown("<h1 style='color:#a5b4fc; margin-bottom:0;'>AradGPT Pro</h1>", unsafe_allow_html=True)
        st.markdown("<p style='color:#94a3b8;'>ورود به نسل جدید هوش مصنوعی</p>", unsafe_allow_html=True)
        
        with st.form("login_form"):
            u = st.text_input("نام کاربری", placeholder="Username")
            p = st.text_input("رمز عبور", type="password", placeholder="Password")
            
            # فاصله
            st.markdown("<br>", unsafe_allow_html=True)
            
            if st.form_submit_button("🚀 ورود به سامانه", type="primary", use_container_width=True):
                user = check_login(u, p)
                if user:
                    st.session_state.user = user
                    st.rerun()
                else:
                    st.error("نام کاربری یا رمز عبور اشتباه است")
        st.markdown('</div>', unsafe_allow_html=True)

def render_dashboard():
    """داشبورد اصلی با ساختار Qwen"""
    db_user = get_user(st.session_state.user["username"])
    if not db_user:
        st.session_state.user = None
        st.rerun()
    
    username, current_balance, role = st.session_state.user["username"], db_user[2], db_user[3]

    # >>>> فراخوانی دکمه‌های شناور <<<<
    inject_floating_action_buttons()

    # --- [SIDEBAR] منوی کناری پیشرفته ---
    with st.sidebar:
        # 1. کارت پروفایل متحرک
        st.markdown(
            f"""
            <div class="user-profile-box">
                <h3>{username}</h3>
                <p>💎 {int(current_balance):,} تومان</p>
            </div>
            """, 
            unsafe_allow_html=True
        )

        # 2. منوی ناوبری اصلی
        options = {
            "chat": "💬 چت هوشمند",
            "image": "🎨 استودیو تصویر",
            "audio": "🎙️ استودیو صدا",
            "wallet": "💳 کیف پول",
        }
        if role == "admin":
            options["admin"] = "⚙️ پنل مدیریت"

        selection = st.radio(
            "Main Menu", 
            options.keys(), 
            format_func=lambda x: options[x],
            label_visibility="collapsed"
        )

        # 3. بخش تاریخچه چت (فقط در تب چت)
        if selection == "chat":
            st.markdown("""
                <div style="margin-top:20px; padding-top:15px; border-top:1px solid rgba(255,255,255,0.1);">
                    <h6 style="color:#94a3b8; font-size:0.85rem; margin-bottom:10px;">🕒 تاریخچه گفتگوها</h6>
                </div>
            """, unsafe_allow_html=True)
            
            # دکمه سبز برای چت جدید
            if st.button("➕ گفتگوی جدید", type="secondary", use_container_width=True):
                 st.session_state.active_session_id = None
                 st.session_state.messages = []
                 st.rerun()
            
            sessions = get_user_sessions(username)[:5]
            if sessions:
                for s in sessions:
                    c1, c2 = st.columns([0.85, 0.15])
                    with c1:
                        # دکمه شیشه‌ای برای سشن‌ها
                        if st.button(f"🗨️ {s[1][:18]}...", key=f"sess_{s[0]}", help=s[1]):
                            st.session_state.active_session_id = s[0]
                            st.session_state.messages = load_session_messages(s[0])
                            st.rerun()
                    with c2:
                        if st.button("✕", key=f"del_{s[0]}"):
                            delete_session(s[0])
                            if st.session_state.active_session_id == s[0]:
                                 st.session_state.active_session_id = None
                                 st.session_state.messages = []
                            st.rerun()
            else:
                st.caption("تاریخچه‌ای موجود نیست")

        # 4. دکمه خروج (پایین صفحه)
        st.markdown("<br>" * 3, unsafe_allow_html=True)
        st.markdown('<div class="logout-btn-container">', unsafe_allow_html=True)
        if st.button("🚪 خروج از حساب", use_container_width=True):
            st.session_state.user = None
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    # --- [HEADER] نوار وضعیت بالا ---
    # شبیه‌سازی هدر با کانتینر
    with st.container():
        h1, h2 = st.columns([3, 1])
        with h1:
            # نمایش تیتر صفحه بر اساس انتخاب
            titles = {"chat": "چت هوشمند", "image": "استودیو گرافیک", "audio": "پردازش صوت", "wallet": "مدیریت مالی", "admin": "پنل ادمین"}
            st.markdown(f"<h2 style='margin:0; color:#f8fafc;'>{titles.get(selection, 'AradGPT')}</h2>", unsafe_allow_html=True)
            st.markdown(f"<p style='margin:0; color:#64748b; font-size:0.9rem;'>نسخه حرفه‌ای | {selection.upper()}</p>", unsafe_allow_html=True)
        with h2:
            # وضعیت اتصال (نمایشی)
            st.markdown("<div style='text-align:left; color:#10b981; font-weight:bold; font-size:0.8rem;'>● Online System</div>", unsafe_allow_html=True)
        st.markdown("<hr style='border-color:rgba(255,255,255,0.1); margin-top:10px;'>", unsafe_allow_html=True)

    # --- [MAIN CONTENT] محتوای اصلی ---
    if not client:
        st.error("⚠️ خطای اتصال: کلید API یافت نشد.")
        return

    # استفاده از Viewها
    if selection == "chat":
        chat.render_chat_page(client, username, current_balance)
    elif selection == "image":
        image.render_image_page(client, username, current_balance)
    elif selection == "audio":
        audio.render_audio_page(client, username, current_balance)
    elif selection == "wallet":
        wallet.render_wallet_page(username, current_balance)
    elif selection == "admin":
        admin.render_admin_page(username)

# ==========================================
# 4. اجرا (EXECUTION)
# ==========================================
if __name__ == "__main__":
    main()