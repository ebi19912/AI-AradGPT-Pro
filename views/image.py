import streamlit as st
from modules.pricing import PRICING_DB, USD_TO_TOMAN
from modules.utils import calculate_image_cost
from modules.database import update_balance, log_usage

def render_image_page(client, username, current_balance):
    # --- هدر صفحه ---
    st.markdown(
        '<div class="modern-card"><h2 style="margin:0; color:#667eea;">🎨 استودیو گرافیک</h2>'
        '<p>تولید تصاویر خلاقانه با هوش مصنوعی</p></div>',
        unsafe_allow_html=True,
    )

    # --- تابع فرمت‌دهی برای نمایش توضیحات مدل ---
    def format_img_model(model_key):
        # دریافت اطلاعات مدل از دیتابیس قیمت‌ها
        info = PRICING_DB.get(model_key, {})
        desc = info.get("desc", "")
        
        # اگر توضیحات وجود داشت، آن را در پرانتز نشان بده
        if desc:
            return f"{model_key}  (✨ {desc})"
        return model_key

    # --- انتخاب مدل و نمایش قیمت ---
    c1, c2 = st.columns([3, 1])
    with c1:
        # فیلتر کردن فقط مدل‌های تصویری
        img_models = sorted([k for k, v in PRICING_DB.items() if v.get("type") == "image"])
        
        # سلکت باکس با قابلیت نمایش توضیحات (format_func)
        mod = st.selectbox(
            "موتور پردازش تصویر", 
            img_models,
            format_func=format_img_model  # <--- تغییر کلیدی اینجاست
        )
    
    with c2:
        cost = calculate_image_cost(mod)
        st.info(f"💎 هزینه هر تصویر:\n{int(cost):,} تومان")

    # --- تنظیمات ورودی ---
    mode = st.radio("حالت عملیات", ["متن به تصویر", "تغییر تصویر (Variation)"], horizontal=True)

    img_f = None
    if mode == "تغییر تصویر (Variation)":
        img_f = st.file_uploader("تصویر PNG را آپلود کنید", type=["png"])
        if img_f:
            st.image(img_f, caption="تصویر ورودی", width=200)

    prompt_text = st.text_area(
        "توصیف تصویر مورد نظر...", 
        height=100, 
        placeholder="مثال: یک لوگوی مدرن برای شرکت هوش مصنوعی با رنگ‌های آبی و بنفش، سبک مینیمال..."
    )

    # --- دکمه اجرا ---
    if st.button("✨ ساخت تصویر", type="primary", use_container_width=True):
        # بررسی موجودی
        if current_balance < cost:
            st.error("موجودی کیف پول شما برای این عملیات کافی نیست.")
            return

        # بررسی ورودی‌ها
        if mode == "تغییر تصویر (Variation)" and not img_f:
            st.error("لطفاً یک تصویر آپلود کنید.")
            return
        if mode == "متن به تصویر" and not prompt_text:
            st.error("لطفاً توصیف تصویر را وارد کنید.")
            return

        try:
            with st.spinner("در حال طراحی و پردازش... (ممکن است تا ۱ دقیقه طول بکشد)"):
                res = None
                if mode == "تغییر تصویر (Variation)":
                    res = client.images.create_variation(
                        image=img_f, 
                        model=mod, 
                        n=1, 
                        size="1024x1024"
                    )
                else:
                    res = client.images.generate(
                        model=mod, 
                        prompt=prompt_text, 
                        size="1024x1024", 
                        n=1
                    )
                
                # نمایش خروجی
                if res and res.data:
                    url = res.data[0].url
                    st.image(url, caption="تصویر تولید شده", use_container_width=True)
                    
                    # کسر هزینه و لاگ
                    update_balance(username, -cost)
                    log_usage(username, mod, "image", cost)
                    st.success(f"تصویر با موفقیت ساخته شد. هزینه: {int(cost)} تومان")
                else:
                    st.error("پاسخی از سرور دریافت نشد.")

        except Exception as e:
            st.error(f"خطا در ارتباط با API: {str(e)}")