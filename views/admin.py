import streamlit as st
import pandas as pd
import io
from PIL import Image
from modules.database import (
    get_pending_payments, process_payment_request,
    add_bank_account, get_bank_accounts, delete_bank_account,
    create_user, get_all_users_df, update_balance, update_user_password, delete_user,
    get_logs_df
)

def render_admin_page(username):
    st.markdown(
        '<div class="modern-card"><h2 style="margin:0; color:var(--primary);">⚙️ پنل مدیریت</h2>'
        "<p style=\"color:#4a5568;\">مدیریت کاربران، تراکنش‌ها و تنظیمات سیستم</p></div>",
        unsafe_allow_html=True,
    )
    
    tab1, tab2, tab3, tab4 = st.tabs(["💳 درخواست‌های واریز", "🏦 بانک‌ها", "👥 کاربران", "📊 آمار و گزارش"])

    # --- تب 1: مدیریت درخواست‌های واریز ---
    with tab1:
        st.subheader("درخواست‌های در انتظار بررسی")
        reqs = get_pending_payments()
        if not reqs:
            st.info("هیچ درخواست جدیدی وجود ندارد.")
        
        for r in reqs:
            rid, user_req, amt, img_bytes, created_at = r
            with st.expander(f"👤 {user_req} | 💰 {amt:,} تومان | 📅 {created_at}"):
                if img_bytes:
                    try:
                        st.image(Image.open(io.BytesIO(img_bytes)), caption="رسید پرداخت", width=300)
                    except Exception:
                        st.error("تصویر ضمیمه‌شده قابل نمایش نیست.")
                
                col_btn1, col_btn2 = st.columns(2)
                if col_btn1.button("✅ تایید و شارژ", key=f"app_{rid}"):
                    if process_payment_request(rid, "APPROVED"):
                        st.success(f"درخواست کاربر {user_req} تایید شد.")
                        st.rerun()
                    else:
                        st.error("خطا در پردازش درخواست.")

                if col_btn2.button("❌ رد درخواست", key=f"rej_{rid}"):
                    process_payment_request(rid, "REJECTED")
                    st.warning("درخواست رد شد.")
                    st.rerun()

    # --- تب 2: مدیریت حساب‌های بانکی ---
    with tab2:
        c1, c2 = st.columns([1, 1])
        with c1:
            st.markdown("### ➕ افزودن حساب جدید")
            with st.form("new_bank_account"):
                b_name = st.text_input("نام بانک")
                o_name = st.text_input("نام صاحب حساب")
                c_num = st.text_input("شماره کارت")
                s_num = st.text_input("شماره شبا (اختیاری)")
                if st.form_submit_button("ثبت حساب"):
                    add_bank_account(b_name, o_name, c_num, s_num)
                    st.success("حساب بانکی جدید اضافه شد.")
                    st.rerun()
        
        with c2:
            st.markdown("### 📋 لیست حساب‌ها")
            accs = get_bank_accounts()
            if not accs.empty:
                for _, row in accs.iterrows():
                    with st.container(border=True):
                        st.write(f"**{row['bank_name']}** - {row['owner_name']}")
                        st.code(row['card_number'])
                        if st.button("حذف حساب", key=f"del_bank_{row['id']}"):
                            delete_bank_account(row["id"])
                            st.rerun()
            else:
                st.info("هیچ حساب بانکی ثبت نشده است.")

    # --- تب 3: مدیریت کاربران ---
    with tab3:
        c_add, c_list = st.columns([1, 2])
        
        with c_add:
            st.markdown("### ➕ کاربر جدید")
            with st.form("create_user_form"):
                nu = st.text_input("نام کاربری")
                np = st.text_input("رمز عبور", type="password")
                nb = st.number_input("شارژ اولیه", min_value=0, step=5000)
                if st.form_submit_button("ایجاد کاربر"):
                    if not nu or not np:
                        st.error("نام کاربری و رمز عبور الزامی است.")
                    elif create_user(nu, np, nb):
                        st.success(f"کاربر {nu} ساخته شد.")
                        st.rerun()
                    else:
                        st.error("این نام کاربری قبلاً گرفته شده است.")

        with c_list:
            st.markdown("### 📋 لیست کاربران")
            users_df = get_all_users_df()
            if not users_df.empty:
                st.dataframe(users_df, use_container_width=True)
                
                st.divider()
                st.markdown("#### 🔧 عملیات روی کاربر خاص")
                target_u = st.selectbox("انتخاب کاربر برای ویرایش", users_df["username"].unique())
                
                act_tabs = st.tabs(["💰 شارژ دستی", "🔑 تغییر رمز", "🗑️ حذف کاربر"])
                
                with act_tabs[0]:
                    charge_amt = st.number_input("مبلغ (تومان) - منفی برای کسر", step=10000, key="adm_chg")
                    if st.button("اعمال موجودی"):
                        update_balance(target_u, charge_amt)
                        st.success(f"موجودی {target_u} به روز شد.")
                        st.rerun()
                
                with act_tabs[1]:
                    new_pass = st.text_input("رمز عبور جدید", type="password", key="adm_pass")
                    if st.button("تغییر رمز"):
                        if update_user_password(target_u, new_pass):
                            st.success("رمز عبور تغییر کرد.")
                        else:
                            st.error("خطا در تغییر رمز.")

                with act_tabs[2]:
                    st.warning("حذف کاربر غیرقابل بازگشت است!")
                    if st.button("حذف دائمی کاربر", type="primary"):
                        if target_u == "admin":
                            st.error("نمی‌توانید ادمین اصلی را حذف کنید.")
                        elif delete_user(target_u):
                            st.success(f"کاربر {target_u} حذف شد.")
                            st.rerun()

    # --- تب 4: آمار و گزارشات ---
    with tab4:
        logs = get_logs_df()
        if not logs.empty:
            total_income = logs['cost_toman'].sum()
            st.metric("مجموع درآمد (تومان)", f"{int(total_income):,}")
            
            st.subheader("ریز تراکنش‌ها")
            st.dataframe(logs, use_container_width=True)
            
            # نمودار ساده (اختیاری)
            try:
                st.bar_chart(logs.groupby("model")["cost_toman"].sum())
            except:
                pass
        else:
            st.info("داده‌ای برای نمایش وجود ندارد.")