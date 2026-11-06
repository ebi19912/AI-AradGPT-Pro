# views/admin.py
"""
پنل مدیریت پیشرفته سیستم AradGPT Pro
مدیریت درخواست‌های مالی، حساب‌های بانکی، کاربران، آمار،
و پیکربندی پویا و زنده ارائه‌دهنده‌های هوش مصنوعی (OpenRouter, GapGPT, OpenAI, DeepSeek, Groq, Custom)
"""

import streamlit as st
import pandas as pd
import io
from PIL import Image
from modules.database import (
    get_pending_payments,
    process_payment_request,
    get_all_payment_requests,
    add_bank_account,
    get_bank_accounts,
    delete_bank_account,
    create_user,
    get_all_users_df,
    update_balance,
    update_user_password,
    update_user_role,
    delete_user,
    get_logs_df,
    get_system_stats,
    get_setting,
    set_setting
)
from modules.config import (
    PROVIDERS,
    get_active_provider_key,
    get_active_base_url,
    get_active_api_key,
    get_usd_to_toman,
    get_welcome_bonus
)
from modules.ai_client import test_api_connection


def render_admin_page(username: str):
    st.markdown(
        '<div class="modern-card">'
        '<h2 style="margin:0; color:#a5b4fc;">⚙️ کنترل پنل مدیریت ارشد</h2>'
        '<p style="color:#94a3b8; margin:4px 0 0 0;">نظارت بر عملکرد سیستم، تراکنش‌های مالی، کاربران و تنظیمات ارائه‌دهنده‌های هوش مصنوعی</p>'
        '</div>',
        unsafe_allow_html=True,
    )

    # --- نمایش شاخص‌های کلیدی (KPIs) ---
    stats = get_system_stats()
    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    with kpi1:
        st.metric("👥 تعداد کل کاربران", f"{stats['total_users']:,} نفر")
    with kpi2:
        st.metric("💰 مجموع درآمد پردازش", f"{int(stats['total_revenue']):,} تومان")
    with kpi3:
        st.metric("⏳ واریزی در انتظار", f"{stats['pending_payments']} مورد")
    with kpi4:
        st.metric("⚡ کل درخواست‌ها", f"{stats['total_requests']:,} فراخوانی")

    tab_pay, tab_bank, tab_users, tab_api, tab_reports = st.tabs([
        "💳 درخواست‌های واریز",
        "🏦 حساب‌های بانکی",
        "👥 مدیریت کاربران",
        "🔌 تنظیمات API و سیستم",
        "📊 آمار و گزارشات"
    ])

    # ==========================================
    # --- تب 1: مدیریت درخواست‌های واریز ---
    # ==========================================
    with tab_pay:
        st.subheader("درخواست‌های شارژ در انتظار بررسی")
        pending_list = get_pending_payments()
        if not pending_list:
            st.info("در حال حاضر هیچ درخواست شارژ جدیدی در انتظار بررسی وجود ندارد.")
        else:
            for item in pending_list:
                rid, req_user, amt, img_bytes, created_at, prev_note = item
                with st.expander(f"👤 کاربر: {req_user} | 💰 مبلغ: {amt:,} تومان | 📅 تاریخ: {created_at}"):
                    c_img, c_actions = st.columns([1, 1.2])
                    with c_img:
                        if img_bytes:
                            try:
                                st.image(Image.open(io.BytesIO(img_bytes)), caption="تصویر فیش بارگذاری شده", use_container_width=True)
                            except Exception:
                                st.error("خطا در بازخوانی تصویر فیش.")
                        else:
                            st.warning("فایلی به عنوان فیش ضمیمه نشده است.")

                    with c_actions:
                        st.markdown(f"**شناسه درخواست:** #{rid}")
                        st.markdown(f"**نام کاربری:** `{req_user}`")
                        st.markdown(f"**مبلغ قابل افزایش:** `{amt:,}` تومان")

                        admin_note = st.text_input("یادداشت یا دلیل (اختیاری):", key=f"note_{rid}", placeholder="مثلاً: شماره پیگیری تایید شد")

                        col_btn1, col_btn2 = st.columns(2)
                        with col_btn1:
                            if st.button("✅ تایید و شارژ حساب", key=f"app_{rid}", type="primary", use_container_width=True):
                                if process_payment_request(rid, "APPROVED", admin_note):
                                    st.success(f"حساب {req_user} با مبلغ {amt:,} تومان شارژ شد.")
                                    st.rerun()
                                else:
                                    st.error("خطا در پردازش تایید.")

                        with col_btn2:
                            if st.button("❌ رد درخواست", key=f"rej_{rid}", use_container_width=True):
                                process_payment_request(rid, "REJECTED", admin_note or "فیش نامعتبر")
                                st.warning("درخواست رد شد.")
                                st.rerun()

        st.divider()
        st.subheader("📋 تاریخچه ۵۰ درخواست اخیر")
        all_reqs_df = get_all_payment_requests(50)
        if not all_reqs_df.empty:
            st.dataframe(all_reqs_df, use_container_width=True)

    # ==========================================
    # --- تب 2: مدیریت حساب‌های بانکی ---
    # ==========================================
    with tab_bank:
        c_new_bank, c_list_bank = st.columns([1, 1.2])
        with c_new_bank:
            st.markdown("### ➕ افزودن حساب بانکی جدید")
            with st.form("new_bank_form"):
                b_name = st.text_input("نام بانک (مثال: بانک ملی، سامان، بلو)")
                o_name = st.text_input("نام و نام خانوادگی صاحب حساب")
                c_num = st.text_input("شماره ۱۶ رقمی کارت")
                s_num = st.text_input("شماره شبا (با IR یا بدون آن - اختیاری)")

                if st.form_submit_button("ثبت شماره حساب", type="primary", use_container_width=True):
                    if not b_name or not o_name or not c_num:
                        st.error("نام بانک، صاحب حساب و شماره کارت الزامی هستند.")
                    else:
                        add_bank_account(b_name.strip(), o_name.strip(), c_num.strip(), s_num.strip())
                        st.success("حساب بانکی با موفقیت ثبت شد.")
                        st.rerun()

        with c_list_bank:
            st.markdown("### 📋 لیست حساب‌های فعال در سامانه")
            banks_df = get_bank_accounts()
            if not banks_df.empty:
                for _, row in banks_df.iterrows():
                    with st.container(border=True):
                        st.write(f"🏦 **{row['bank_name']}** — {row['owner_name']}")
                        st.code(row['card_number'])
                        if row.get('sheba_number'):
                            st.caption(f"شبا: {row['sheba_number']}")
                        if st.button("🗑️ حذف این حساب", key=f"del_b_{row['id']}"):
                            delete_bank_account(row["id"])
                            st.rerun()
            else:
                st.info("هنوز حساب بانکی در سامانه اضافه نشده است.")

    # ==========================================
    # --- تب 3: مدیریت کاربران ---
    # ==========================================
    with tab_users:
        u_col1, u_col2 = st.columns([1, 1.8])
        with u_col1:
            st.markdown("### ➕ ایجاد دستی کاربر")
            with st.form("admin_create_user"):
                new_u = st.text_input("نام کاربری")
                new_p = st.text_input("رمز عبور اولیه", type="password")
                new_b = st.number_input("شارژ اولیه (تومان)", min_value=0, value=20000, step=5000)
                new_role = st.selectbox("نقش کاربر", ["user", "admin"])

                if st.form_submit_button("ساخت کاربر", type="primary", use_container_width=True):
                    if not new_u or not new_p:
                        st.error("نام کاربری و رمز عبور الزامی است.")
                    elif create_user(new_u, new_p, new_b, new_role):
                        st.success(f"کاربر {new_u} با موفقیت ساخته شد.")
                        st.rerun()
                    else:
                        st.error("نام کاربری تکراری است.")

        with u_col2:
            st.markdown("### 📋 فهرست کاربران سامانه")
            users_df = get_all_users_df()
            search_query = st.text_input("🔍 جستجوی نام کاربری:", placeholder="نام کاربری را تایپ کنید...")
            if search_query:
                users_df = users_df[users_df["username"].str.contains(search_query.strip().lower(), na=False)]

            st.dataframe(users_df, use_container_width=True)

            if not users_df.empty:
                st.markdown("#### 🔧 عملیات مدیریتی روی حساب کاربر")
                chosen_user = st.selectbox("انتخاب کاربر هدف:", users_df["username"].tolist())

                u_tabs = st.tabs(["💰 تغییر موجودی", "🔑 بازنشانی رمز", "🛡️ تغییر سطح دسترسی", "🗑️ حذف حساب"])

                with u_tabs[0]:
                    amt_change = st.number_input("مبلغ جهت افزایش یا کسر (مقادیر منفی برای کسر):", step=10000, key="u_chg")
                    if st.button("اعمال تغییر موجودی"):
                        update_balance(chosen_user, amt_change)
                        st.success(f"موجودی {chosen_user} بروزرسانی شد.")
                        st.rerun()

                with u_tabs[1]:
                    new_password_val = st.text_input("رمز عبور جدید:", type="password", key="u_pass")
                    if st.button("تغییر رمز عبور"):
                        if update_user_password(chosen_user, new_password_val):
                            st.success(f"گذرواژه {chosen_user} تغییر یافت.")
                        else:
                            st.error("خطا در تغییر گذرواژه.")

                with u_tabs[2]:
                    role_choice = st.selectbox("سطح دسترسی جدید:", ["user", "admin"], key="u_role")
                    if st.button("ذخیره سطح دسترسی"):
                        if update_user_role(chosen_user, role_choice):
                            st.success(f"نقش {chosen_user} به {role_choice} تغییر یافت.")
                            st.rerun()

                with u_tabs[3]:
                    st.warning("حذف کاربر غیرقابل بازگشت است و تمام پیام‌های چت کاربر پاک خواهد شد.")
                    if st.button(f"حذف دائمی کاربر {chosen_user}", type="primary"):
                        if chosen_user == "admin":
                            st.error("حساب ادمین اصلی قابل حذف نیست.")
                        elif delete_user(chosen_user):
                            st.success(f"کاربر {chosen_user} حذف گردید.")
                            st.rerun()

    # ==========================================
    # --- تب 4: تنظیمات API و سیستم ---
    # ==========================================
    with tab_api:
        st.markdown("### 🔌 پیکربندی ارائه‌دهنده هوش مصنوعی و کلیدهای API")
        st.info(
            "در این بخش می‌توانید ارائه‌دهنده سرویس هوش مصنوعی را به صورت زنده تغییر دهید. "
            "می‌توانید از **OpenRouter** (دسترسی به تمامی مدل‌های دنیا), **GapGPT** (سرویس چندرسانه‌ای داخلی), **OpenAI رسمی**, **DeepSeek**, یا **آدرس سفارشی خودتان (Custom Base URL / Local LLM)** استفاده نمایید."
        )

        current_prov = get_active_provider_key()
        current_base_url = get_active_base_url()
        current_api_key = get_active_api_key()
        current_usd_rate = get_usd_to_toman()
        current_welcome_bonus = get_welcome_bonus()

        prov_keys = list(PROVIDERS.keys())
        default_prov_idx = prov_keys.index(current_prov) if current_prov in prov_keys else 0

        c_p1, c_p2 = st.columns([1.5, 1])

        with c_p1:
            selected_provider_key = st.selectbox(
                "انتخاب ارائه‌دهنده پیش‌فرض (Active Provider)",
                prov_keys,
                index=default_prov_idx,
                format_func=lambda k: PROVIDERS[k]["name"]
            )
            provider_meta = PROVIDERS[selected_provider_key]
            st.caption(f"💡 {provider_meta['description']}")

            suggested_url = provider_meta["base_url"]
            target_base_url = st.text_input(
                "آدرس سرور API (Base URL)",
                value=current_base_url if current_prov == selected_provider_key else suggested_url,
                help="آدرس اندپوینت سازگار با فرمت OpenAI (معمولاً با پسوند /v1)"
            )

            target_api_key = st.text_input(
                "کلید اختصاصی API (API Key)",
                value=current_api_key,
                type="password",
                placeholder="sk-or-v1-... یا کلید ارائه‌دهنده",
                help="کلید دسترسی به ارائه‌دهنده انتخابی"
            )

        with c_p2:
            st.markdown("#### ⚡ تست زنده اتصال به API")
            st.caption("پیش از ذخیره می‌توانید از صحت اتصال و کلید API اطمینان حاصل کنید:")
            if st.button("🚀 تست برقراری اتصال (Ping)", use_container_width=True):
                with st.spinner("در حال ارسال درخواست تست..."):
                    success, msg, latency, models = test_api_connection(target_api_key, target_base_url)
                    if success:
                        st.success(f"✅ {msg}")
                        if models:
                            st.caption(f"نمونه مدل‌های شناسایی‌شده: {', '.join(models[:4])}")
                    else:
                        st.error(f"❌ {msg}")

            st.divider()
            st.markdown("#### 💵 پارامترهای مالی و اقتصادی")
            target_usd_rate = st.number_input(
                "نرخ تبدیل دلار به تومان",
                min_value=10000,
                max_value=300000,
                value=int(current_usd_rate),
                step=1000,
                help="برای محاسبه دقیق بهای توکن‌های ورودی و خروجی"
            )

            target_welcome_bonus = st.number_input(
                "هدیه خوش‌آمدگویی برای ثبت‌نام جدید (تومان)",
                min_value=0,
                value=int(current_welcome_bonus),
                step=5000,
                help="این مبلغ به محض ایجاد حساب جدید به کیف پول کاربر اضافه می‌شود."
            )

        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("💾 ذخیره تغییرات و اعمال در کل سامانه", type="primary", use_container_width=True):
            set_setting("ACTIVE_PROVIDER", selected_provider_key)
            set_setting("AI_BASE_URL", target_base_url.strip())
            set_setting("AI_API_KEY", target_api_key.strip())
            set_setting("USD_TO_TOMAN", str(target_usd_rate))
            set_setting("WELCOME_BONUS", str(target_welcome_bonus))

            # پاک‌سازی کش کلاینت برای ایجاد مجدد با تنظیمات نو
            st.cache_resource.clear()
            st.success("✅ کلیه تنظیمات با موفقیت در پایگاه‌داده ذخیره شد و بدون نیاز به ریست سرور اعمال گردید!")
            st.rerun()

    # ==========================================
    # --- تب 5: آمار و گزارشات جامع ---
    # ==========================================
    with tab_reports:
        st.markdown("### 📊 گزارش عملکرد و تحلیل مصارف سیستم")
        logs_df = get_logs_df(limit=300)

        if not logs_df.empty:
            c_chart1, c_chart2 = st.columns(2)
            with c_chart1:
                st.markdown("##### تفکیک مصرف به تفکیک مدل‌ها (تومان)")
                model_costs = logs_df[logs_df["type"] != "deposit"].groupby("model")["cost_toman"].sum()
                if not model_costs.empty:
                    st.bar_chart(model_costs)

            with c_chart2:
                st.markdown("##### تفکیک مصرف به تفکیک نوع سرویس")
                type_costs = logs_df[logs_df["type"] != "deposit"].groupby("type")["cost_toman"].sum()
                if not type_costs.empty:
                    st.bar_chart(type_costs)

            st.divider()
            st.subheader("📋 جدول لاگ تراکنش‌ها و درخواست‌ها")
            st.dataframe(logs_df, use_container_width=True)

            csv_logs = logs_df.to_csv(index=False).encode("utf-8-sig")
            st.download_button(
                "📥 دریافت تمام لاگ‌ها (CSV)",
                data=csv_logs,
                file_name="aradgpt_system_logs.csv",
                mime="text/csv"
            )
        else:
            st.info("هنوز لاگی برای نمایش نمودارها وجود ندارد.")
