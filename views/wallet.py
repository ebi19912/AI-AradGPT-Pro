import streamlit as st
from modules.database import (
    get_bank_accounts,
    submit_payment_request,
    get_logs_df
)

def render_wallet_page(username, current_balance):
    # --- هدر کیف پول ---
    st.markdown(
        f'<div class="wallet-card"><h2>موجودی فعلی شما</h2><h1>{int(current_balance):,} تومان</h1>'
        "<p>وضعیت مصرف و شارژ را در این بخش بررسی کنید.</p></div>",
        unsafe_allow_html=True,
    )

    c1, c2 = st.columns([1.5, 1])
    
    # --- بخش شماره حساب‌ها ---
    with c1:
        st.markdown(
            '<div class="modern-card"><h3>🏦 شماره حساب‌ها</h3>'
            '<p style="color:#4a5568;">برای شارژ حساب، یکی از حساب‌های زیر را انتخاب کنید.</p>',
            unsafe_allow_html=True,
        )
        banks = get_bank_accounts()
        if not banks.empty:
            for _, r in banks.iterrows():
                st.markdown(
                    f'<div class="bank-card"><h4>{r["bank_name"]}</h4><p>{r["owner_name"]}</p></div>',
                    unsafe_allow_html=True,
                )
                if r["card_number"]:
                    st.code(r["card_number"])
        else:
            st.warning("هنوز حسابی ثبت نشده است.")
        st.markdown("</div>", unsafe_allow_html=True)

    # --- بخش ثبت فیش ---
    with c2:
        st.markdown(
            '<div class="modern-card"><h3>📝 ثبت فیش پرداختی</h3>'
            '<p style="color:#4a5568;">پس از انتقال وجه، تصویر رسید را ارسال نمایید.</p>',
            unsafe_allow_html=True,
        )
        with st.form("deposit"):
            amt = st.number_input("مبلغ (تومان)", 10000, step=10000)
            img = st.file_uploader("تصویر رسید")
            if st.form_submit_button("ارسال درخواست", type="primary"):
                submit_payment_request(username, amt, img.getvalue() if img else None)
                st.success("درخواست شما ثبت شد؛ پس از بررسی، شارژ اعمال می‌گردد.")
        st.markdown("</div>", unsafe_allow_html=True)

    st.divider()

    # --- جدول تراکنش‌ها ---
    logs = get_logs_df()
    if not logs.empty:
        # فیلتر کردن لاگ‌های مربوط به کاربر جاری
        ul = logs[logs["username"] == username].sort_values("id", ascending=False).head(10)
        if not ul.empty:
            st.markdown("### 📊 آخرین تراکنش‌ها")
            st.dataframe(ul[["timestamp", "model", "cost_toman"]], width=None, use_container_width=True)
        else:
            st.info("تاکنون فعالیتی ثبت نشده است.")
    else:
        st.info("هنوز هیچ لاگی در سیستم ثبت نشده است.")