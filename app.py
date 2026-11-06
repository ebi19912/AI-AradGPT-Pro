# app.py
"""
سامانه جامع هوش مصنوعی چندرسانه‌ای AradGPT Pro
نقطه ورودی اصلی نرم‌افزار با قابلیت ورود، ثبت‌نام، پنل کاربری، انتخاب ارائه‌دهنده و داشبورد کامل
"""

import os
import streamlit as st
from openai import OpenAI

# ماژول‌های داخلی سیستم
from modules.database import (
    init_db,
    get_user,
    get_user_sessions,
    delete_session,
    load_session_messages
)
from modules.auth import check_login, register_user
from modules.ai_client import get_client, get_current_provider_info
from modules.ui import setup_page_config, inject_floating_action_buttons
from modules.config import get_welcome_bonus

# ویوهای مختلف برنامه
from views import chat, image, audio, wallet, admin

# ==========================================
# 1. تنظیمات اولیه صفحه (PAGE SETUP)
# ==========================================
LOGO_PATH = os.path.join("assets", "logo.png")
PAGE_ICON = LOGO_PATH if os.path.exists(LOGO_PATH) else "🤖"

setup_page_config(PAGE_ICON)
init_db()

# متغیر سشن کاربر
if "user" not in st.session_state:
    st.session_state.user = None


# ==========================================
# 2. لاجیک ورود و ثبت‌نام (AUTH VIEWS)
# ==========================================
def render_auth_page():
    """صفحه ورود و ثبت نام شیشه‌ای و مدرن با پشتیبانی از هدیه ثبت‌نام"""
    col1, col2, col3 = st.columns([1, 1.4, 1])
    with col2:
        st.markdown(
            """
            <div class="modern-card" style="text-align:center; padding: 32px 24px;">
                <h1 style="color:#a5b4fc; margin-bottom:4px; font-weight:800; font-size:2.2rem;">AradGPT Pro</h1>
                <p style="color:#94a3b8; font-size:0.95rem; margin-bottom:20px;">دستیار هوشمند، استودیو چندرسانه‌ای و مرکز پردازش‌های AI</p>
            """,
            unsafe_allow_html=True
        )

        tab_login, tab_register = st.tabs(["🔑 ورود به سامانه", "📝 ثبت‌نام کاربر جدید"])

        # --- فرم ورود ---
        with tab_login:
            with st.form("login_form"):
                u = st.text_input("نام کاربری", placeholder="Username")
                p = st.text_input("رمز عبور", type="password", placeholder="Password")

                st.markdown("<br>", unsafe_allow_html=True)
                if st.form_submit_button("🚀 ورود به حساب کاربری", type="primary", use_container_width=True):
                    user_data = check_login(u, p)
                    if user_data:
                        st.session_state.user = user_data
                        st.session_state.active_session_id = None
                        st.session_state.messages = []
                        st.success(f"خوش آمدید، {user_data['username']} عزیز!")
                        st.rerun()
                    else:
                        st.error("نام کاربری یا رمز عبور اشتباه است.")

        # --- فرم ثبت‌نام ---
        with tab_register:
            bonus = get_welcome_bonus()
            if bonus > 0:
                st.caption(f"🎁 به مناسبت ثبت‌نام اولیه، حساب شما به مبلغ **{bonus:,} تومان** به صورت رایگان شارژ خواهد شد.")

            with st.form("register_form"):
                reg_u = st.text_input("نام کاربری دلخواه (حروف انگلیسی یا عدد)", placeholder="e.g. arad_user")
                reg_p = st.text_input("رمز عبور (حداقل ۶ کاراکتر)", type="password", placeholder="••••••••")
                reg_cp = st.text_input("تکرار رمز عبور", type="password", placeholder="••••••••")

                st.markdown("<br>", unsafe_allow_html=True)
                if st.form_submit_button("✨ ساخت حساب و دریافت هدیه", type="primary", use_container_width=True):
                    success, user_obj, msg = register_user(reg_u, reg_p, reg_cp)
                    if success:
                        st.session_state.user = user_obj
                        st.session_state.active_session_id = None
                        st.session_state.messages = []
                        st.success(msg)
                        st.rerun()
                    else:
                        st.error(msg)

        st.markdown('</div>', unsafe_allow_html=True)


# ==========================================
# 3. داشبورد اصلی (DASHBOARD & SIDEBAR)
# ==========================================
def render_dashboard():
    """داشبورد اصلی نرم‌افزار با سایدبار هوشمند، نوار وضعیت و پنل‌ها"""
    username = st.session_state.user["username"]
    db_user = get_user(username)

    if not db_user:
        st.session_state.user = None
        st.rerun()

    current_balance = float(db_user[2])
    role = str(db_user[3]).lower()
    client = get_client()
    provider_info = get_current_provider_info()

    # --- سایدبار ناوبری ---
    with st.sidebar:
        # کارت مشخصات کاربر
        role_label = "🛡️ مدیر ارشد" if role == "admin" else "👤 کاربر سامانه"
        st.markdown(
            f"""
            <div class="user-profile-box">
                <span style="font-size:0.8rem; color:#94a3b8;">{role_label}</span>
                <h3>{username}</h3>
                <p>💎 {int(current_balance):,} تومان</p>
            </div>
            """,
            unsafe_allow_html=True
        )

        # منوی ناوبری اصلی
        menu_options = {
            "chat": "💬 چت هوشمند",
            "image": "🎨 استودیو تصویر",
            "audio": "🎙️ استودیو صدا",
            "wallet": "💳 کیف پول و شارژ",
        }
        if role == "admin":
            menu_options["admin"] = "⚙️ پنل مدیریت"

        selection = st.radio(
            "Main Menu",
            options=list(menu_options.keys()),
            format_func=lambda x: menu_options[x],
            label_visibility="collapsed"
        )

        # بخش تاریخچه گفتگوها (فقط در تب چت)
        if selection == "chat":
            st.markdown(
                """
                <div style="margin-top:20px; padding-top:14px; border-top:1px solid rgba(255,255,255,0.08);">
                    <h6 style="color:#94a3b8; font-size:0.85rem; margin-bottom:10px;">🕒 تاریخچه گفتگوها</h6>
                </div>
                """,
                unsafe_allow_html=True
            )

            if st.button("➕ گفتگوی جدید", use_container_width=True):
                st.session_state.active_session_id = None
                st.session_state.messages = []
                st.rerun()

            sessions = get_user_sessions(username)[:8]
            if sessions:
                for s in sessions:
                    sess_id, sess_title, sess_date = s
                    c1, c2 = st.columns([0.84, 0.16])
                    with c1:
                        display_title = (sess_title[:20] + "...") if len(sess_title) > 20 else sess_title
                        if st.button(f"🗨️ {display_title}", key=f"sess_{sess_id}", help=sess_title, use_container_width=True):
                            st.session_state.active_session_id = sess_id
                            st.session_state.messages = load_session_messages(sess_id)
                            st.rerun()
                    with c2:
                        if st.button("✕", key=f"del_{sess_id}"):
                            delete_session(sess_id)
                            if st.session_state.get("active_session_id") == sess_id:
                                st.session_state.active_session_id = None
                                st.session_state.messages = []
                            st.rerun()
            else:
                st.caption("هنوز گفتگویی ثبت نشده است.")

        # دکمه خروج در انتهای سایدبار
        st.markdown("<br>" * 2, unsafe_allow_html=True)
        if st.button("🚪 خروج از حساب", use_container_width=True):
            st.session_state.user = None
            st.session_state.active_session_id = None
            st.session_state.messages = []
            st.rerun()

    # --- نوار وضعیت و هدر بالا ---
    with st.container():
        h1, h2 = st.columns([3, 1.2])
        with h1:
            titles = {
                "chat": "استودیو چت هوشمند",
                "image": "استودیو گرافیک و تولید تصویر",
                "audio": "استودیو صوت و پردازش صدا",
                "wallet": "کیف پول و مدیریت مالی",
                "admin": "کنترل پنل مدیریت سامانه"
            }
            st.markdown(f"<h2 style='margin:0; color:#f8fafc;'>{titles.get(selection, 'AradGPT Pro')}</h2>", unsafe_allow_html=True)
            st.markdown(f"<p style='margin:2px 0 0 0; color:#64748b; font-size:0.85rem;'>سامانه نسخه حرفه‌ای ۲.۰ | پنل {selection.upper()}</p>", unsafe_allow_html=True)

        with h2:
            status_color = "#10b981" if client else "#f59e0b"
            prov_name = provider_info["name"].split(" ")[0]
            st.markdown(
                f"""
                <div style='text-align:left; color:{status_color}; font-weight:600; font-size:0.85rem; padding-top:6px;'>
                    ● اتصال: {prov_name}
                </div>
                """,
                unsafe_allow_html=True
            )
        st.markdown("<hr style='border-color:rgba(255,255,255,0.08); margin:8px 0 16px 0;'>", unsafe_allow_html=True)

    # --- بررسی وضعیت کلاینت هوش مصنوعی ---
    if not client:
        if role == "admin":
            st.warning("⚠️ کلید API هوش مصنوعی تنظیم نشده است. می‌توانید به عنوان مدیر از تب **پنل مدیریت > تنظیمات API** کلید خود را وارد کنید.")
        else:
            st.error("⚠️ در حال حاضر ارتباط با سرویس هوش مصنوعی برقرار نیست. لطفاً با مدیر سیستم تماس حاصل فرمایید.")

    # --- رندر کردن ویو انتخاب شده ---
    if selection == "chat":
        chat.render_chat_page(client, username, current_balance)
    elif selection == "image":
        image.render_image_page(client, username, current_balance)
    elif selection == "audio":
        audio.render_audio_page(client, username, current_balance)
    elif selection == "wallet":
        wallet.render_wallet_page(username, current_balance)
    elif selection == "admin":
        if role == "admin":
            admin.render_admin_page(username)
        else:
            st.error("شما مجوز دسترسی به این بخش را ندارید.")


# ==========================================
# 4. اجرای برنامه (ENTRY POINT)
# ==========================================
def main():
    if not st.session_state.user:
        render_auth_page()
    else:
        render_dashboard()


if __name__ == "__main__":
    main()
