# views/wallet.py
"""
ویوی کیف پول و مدیریت مالی کاربر (Wallet & Financial Hub)
نمایش موجودی زنده، اطلاعات کارت‌های بانکی، ارسال فیش واریزی، پیگیری وضعیت درخواست‌ها و گزارش تراکنش‌ها
"""

import streamlit as st
import pandas as pd
from modules.database import (
    get_bank_accounts,
    submit_payment_request,
    get_user_payment_requests,
    get_user_logs_df,
    get_user
)

QUICK_AMOUNTS = [50000, 100000, 200000, 500000]


def render_wallet_page(username: str, current_balance: float):
    # دریافت آخرین موجودی تازه از دیتابیس
    db_u = get_user(username)
    latest_balance = db_u[2] if db_u else current_balance

    st.markdown(
        f"""
        <div class="wallet-card">
            <h2>موجودی کیف پول شما</h2>
            <h1>{int(latest_balance):,} تومان</h1>
            <p style="color:#94a3b8; font-size:0.95rem; margin-top:6px;">برای استفاده نامحدود از هوش مصنوعی، حساب خود را شارژ فرمایید.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    tab_charge, tab_requests, tab_history = st.tabs(["💳 افزایش موجودی (واریز)", "📋 وضعیت درخواست‌های شارژ من", "📊 تاریخچه تراکنش‌ها و مصرف"])

    # --- تب 1: افزایش موجودی ---
    with tab_charge:
        c1, c2 = st.columns([1.3, 1])

        # بخش شماره حساب‌ها
        with c1:
            st.markdown(
                """
                <div class="modern-card">
                    <h3 style="margin-top:0; color:#a5b4fc;">🏦 اطلاعات حساب‌های واریز</h3>
                    <p style="color:#94a3b8; font-size:0.88rem;">مبلغ مورد نظر را به یکی از شماره کارت‌های رسمی زیر واریز نموده و فیش را در فرم روبه‌رو ثبت نمایید:</p>
                """,
                unsafe_allow_html=True,
            )
            banks = get_bank_accounts()
            if not banks.empty:
                for _, r in banks.iterrows():
                    st.markdown(
                        f"""
                        <div class="bank-card">
                            <b style="color:#f8fafc; font-size:1rem;">{r['bank_name']}</b> — <span style="color:#cbd5e1;">به نام {r['owner_name']}</span>
                            <div style="margin-top:8px;">
                                <span style="font-size:0.8rem; color:#94a3b8;">شماره کارت (جهت کپی کلیک کنید):</span>
                            </div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
                    st.code(r["card_number"])
                    if r.get("sheba_number") and str(r["sheba_number"]).strip():
                        st.caption(f"شماره شبا: {r['sheba_number']}")
            else:
                st.info("در حال حاضر حسابی توسط مدیریت ثبت نشده است. لطفاً با پشتیبانی در تماس باشید.")
            st.markdown("</div>", unsafe_allow_html=True)

        # فرم ثبت فیش
        with c2:
            st.markdown(
                """
                <div class="modern-card">
                    <h3 style="margin-top:0; color:#a5b4fc;">📝 ثبت فیش پرداختی</h3>
                    <p style="color:#94a3b8; font-size:0.88rem;">تصویر فیش یا رسید انتقال را به همراه مبلغ دقیق وارد فرمایید:</p>
                """,
                unsafe_allow_html=True,
            )

            # دکمه‌های مبالغ سریع
            st.markdown("<span style='font-size:0.85rem; color:#94a3b8;'>مبالغ پرکاربرد:</span>", unsafe_allow_html=True)
            q_cols = st.columns(len(QUICK_AMOUNTS))
            for i, q_amt in enumerate(QUICK_AMOUNTS):
                with q_cols[i]:
                    if st.button(f"{q_amt//1000}هزار", key=f"q_{i}", use_container_width=True):
                        st.session_state.selected_deposit_amt = q_amt

            deposit_val = st.session_state.pop("selected_deposit_amt", 50000)

            with st.form("deposit_form"):
                amt = st.number_input(
                    "مبلغ واریز شده (تومان)",
                    min_value=10000,
                    value=deposit_val,
                    step=10000
                )
                receipt_file = st.file_uploader(
                    "بارگذاری تصویر فیش بانکی (JPG / PNG)",
                    type=["jpg", "jpeg", "png"]
                )

                submit_btn = st.form_submit_button("📤 ارسال درخواست شارژ", type="primary", use_container_width=True)
                if submit_btn:
                    if not receipt_file:
                        st.error("لطفاً تصویر فیش واریزی خود را پیوست نمایید.")
                    else:
                        img_bytes = receipt_file.getvalue()
                        submit_payment_request(username, amt, img_bytes)
                        st.success("✅ فیش شما با موفقیت ثبت شد! پس از بررسی توسط تیم مالی، کیف پول شما بلافاصله شارژ خواهد شد.")

            st.markdown("</div>", unsafe_allow_html=True)

    # --- تب 2: پیگیری وضعیت درخواست‌ها ---
    with tab_requests:
        st.markdown("### 📋 سوابق درخواست‌های افزایش موجودی شما")
        user_reqs = get_user_payment_requests(username)
        if not user_reqs.empty:
            for _, r in user_reqs.iterrows():
                status_raw = r["status"]
                if status_raw == "APPROVED":
                    status_badge = '<span class="badge-approved">✅ تایید و شارژ شده</span>'
                elif status_raw == "REJECTED":
                    status_badge = '<span class="badge-rejected">❌ رد شده</span>'
                else:
                    status_badge = '<span class="badge-pending">⏳ در انتظار بررسی ادمین</span>'

                with st.container(border=True):
                    c_info1, c_info2 = st.columns([2, 1])
                    with c_info1:
                        st.markdown(f"**شناسه پیگیری:** #{r['id']} | **مبلغ:** {int(r['amount']):,} تومان")
                        st.caption(f"📅 تاریخ ثبت: {r['created_at']}")
                        if r.get("admin_note"):
                            st.info(f"پیام مدیریت: {r['admin_note']}")
                    with c_info2:
                        st.markdown(f"<div style='text-align:left; margin-top:10px;'>{status_badge}</div>", unsafe_allow_html=True)
        else:
            st.info("تاکنون هیچ درخواست شارژی از جانب شما ثبت نشده است.")

    # --- تب 3: تاریخچه تراکنش‌ها ---
    with tab_history:
        st.markdown("### 📊 ریز مصارف و تراکنش‌های اخیر")
        user_logs = get_user_logs_df(username, limit=100)
        if not user_logs.empty:
            st.dataframe(
                user_logs.rename(columns={
                    "id": "شناسه",
                    "model": "سرویس / مدل",
                    "type": "نوع عملیات",
                    "cost_toman": "هزینه (تومان)",
                    "timestamp": "زمان تراکنش"
                }),
                use_container_width=True
            )

            # امکان دانلود اکسل/CSV
            csv_data = user_logs.to_csv(index=False).encode("utf-8-sig")
            st.download_button(
                "📥 دریافت گزارش به صورت CSV",
                data=csv_data,
                file_name=f"aradgpt_transactions_{username}.csv",
                mime="text/csv"
            )
        else:
            st.info("هنوز تراکنش مصرفی برای حساب کاربری شما ثبت نشده است.")
