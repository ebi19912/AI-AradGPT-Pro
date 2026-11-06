# views/image.py
"""
استودیو گرافیک و تولید تصویر (Image Studio)
پشتیبانی از مدل‌های DALL-E 3, Flux.1 Schnell/Dev, Imagen 4 و ساخت انواع تصاویر با گالری تاریخچه
"""

import streamlit as st
from typing import List
from modules.pricing import PRICING_DB, calculate_image_cost, get_model_info
from modules.database import update_balance, log_usage, save_image_history, get_user_images_history
from modules.config import get_active_provider_key, PROVIDERS

STYLE_PRESETS = {
    "بدون سبک خاص": "",
    "واقع‌گرایانه (Photorealistic)": "photorealistic, 8k resolution, highly detailed, professional photography, cinematic lighting",
    "هنر دیجیتال (Digital Art)": "digital art, trending on artstation, vibrant colors, masterpiece, smooth illustration",
    "سینمایی (Cinematic)": "cinematic shot, dramatic atmosphere, anamorphic lens, shallow depth of field, hyper-detailed",
    "انیمه / مانگا (Anime Style)": "anime style, makoto shinkai aesthetic, high quality animation, expressive, vibrant",
    "رندر سه‌بعدی (3D Render)": "3D render, octane render, unreal engine 5, clay or metallic textures, volumetric lighting",
    "مینیمال و مدرن (Minimalist)": "minimalist art, clean lines, elegant aesthetic, modern graphic design, vector style"
}


def render_image_page(client, username: str, current_balance: float):
    st.markdown(
        '<div class="modern-card">'
        '<h2 style="margin:0; color:#a5b4fc;">🎨 استودیو گرافیک و تولید تصویر</h2>'
        '<p style="color:#94a3b8; margin:4px 0 0 0;">خلق تصاویر شگفت‌انگیز، مفهومی و هنری با قدرت هوش مصنوعی</p>'
        '</div>',
        unsafe_allow_html=True,
    )

    prov_key = get_active_provider_key()
    prov_info = PROVIDERS.get(prov_key, {})
    if not prov_info.get("supports_images", False) and "openrouter" in prov_key:
        st.warning(
            "⚠️ ارائه‌دهنده فعال سیستم شما در حال حاضر روی **OpenRouter** تنظیم شده است. "
            "برخی اندپوینت‌های متنی اوپن‌روتر از استاندارد `/v1/images/generations` پشتیبانی نمی‌کنند. "
            "برای استفاده حداکثری از استودیو تصویر، می‌توانید در پنل ادمین ارائه‌دهنده را روی **GapGPT** یا **OpenAI** تنظیم فرمایید."
        )

    tab_create, tab_gallery = st.tabs(["✨ ساخت تصویر جدید", "🖼️ گالری و تصاویر قبلی من"])

    with tab_create:
        _render_create_tab(client, username, current_balance)

    with tab_gallery:
        _render_gallery_tab(username)


def _render_create_tab(client, username: str, current_balance: float):
    # فیلتر مدل‌های تصویری
    img_models = sorted([k for k, v in PRICING_DB.items() if v.get("type") == "image"])
    if not img_models:
        img_models = ["dall-e-3", "dall-e-2", "gapgpt/flux.1-schnell"]

    def format_img_model(m_key: str) -> str:
        desc = PRICING_DB.get(m_key, {}).get("desc", "")
        return f"{m_key}  (✨ {desc})" if desc else m_key

    c1, c2 = st.columns([3, 1])
    with c1:
        selected_model = st.selectbox(
            "موتور پردازش و هوش مصنوعی تصویر",
            img_models,
            index=0 if "dall-e-3" not in img_models else img_models.index("dall-e-3"),
            format_func=format_img_model
        )

    cost = calculate_image_cost(selected_model)
    with c2:
        st.markdown(
            f"""
            <div style="background:rgba(255,255,255,0.03); border:1px solid rgba(255,255,255,0.08); border-radius:12px; padding:10px; text-align:center;">
                <span style="font-size:0.8rem; color:#94a3b8;">💎 تعرفه هر تصویر:</span><br>
                <b style="color:#10b981; font-size:1.1rem;">{int(cost):,} تومان</b>
            </div>
            """,
            unsafe_allow_html=True
        )

    col_mode, col_size, col_quality = st.columns([1.5, 1, 1])
    with col_mode:
        mode = st.radio("حالت عملیات", ["متن به تصویر (Text-to-Image)", "تغییر تصویر (Variation)"], horizontal=True)

    with col_size:
        size_choice = st.selectbox(
            "ابعاد تصویر",
            ["1024x1024 (مربع)", "1024x1792 (عمودی)", "1792x1024 (افقی)"]
        )
        api_size = size_choice.split(" ")[0]

    with col_quality:
        quality_choice = st.selectbox("کیفیت خروجی", ["standard", "hd"], index=0)

    img_file = None
    if mode.startswith("تغییر تصویر"):
        st.info("نکته: قابلیت تغییر تصویر (Variation) به طور معمول توسط مدل dall-e-2 پشتیبانی می‌شود.")
        img_file = st.file_uploader("تصویر اولیه را انتخاب کنید (فرمت PNG)", type=["png"])
        if img_file:
            st.image(img_file, caption="تصویر مرجع", width=220)

    col_style, col_enhance = st.columns([1.5, 1])
    with col_style:
        chosen_style = st.selectbox("سبک هنری و استایل (اختیاری)", list(STYLE_PRESETS.keys()), index=0)

    prompt_text = st.text_area(
        "توصیف تصویر مورد نظر (Prompt)",
        height=110,
        placeholder="مثال: یک فضانورد با کلاه‌خود شیشه‌ای در حال کاوش در دشت‌های بنفش کهکشان آندرومدا، نور ملایم ستاره‌ها..."
    )

    if st.button("🚀 ساخت و تولید تصویر", type="primary", use_container_width=True):
        if current_balance < cost:
            st.error(f"موجودی کیف پول شما کافی نیست. هزینه این عملیات {int(cost):,} تومان می‌باشد.")
            return

        if not client:
            st.error("ارتباط با سرور هوش مصنوعی برقرار نیست.")
            return

        if mode.startswith("تغییر تصویر") and not img_file:
            st.error("لطفاً یک تصویر مرجع PNG آپلود فرمایید.")
            return

        if mode.startswith("متن به تصویر") and not prompt_text.strip():
            st.error("لطفاً توصیف تصویر مورد نظر خود را بنویسید.")
            return

        # ترکیب سبک با پرامپت
        full_prompt = prompt_text.strip()
        style_addition = STYLE_PRESETS.get(chosen_style, "")
        if style_addition:
            full_prompt += f", {style_addition}"

        try:
            with st.spinner("هوش مصنوعی در حال طراحی و رندر تصویر است... (حدود ۱۰ الی ۳۰ ثانیه)"):
                res = None
                if mode.startswith("تغییر تصویر"):
                    # آماده‌سازی بایت‌های تصویر برای کلاینت OpenAI
                    img_payload = (img_file.name, img_file.getvalue(), "image/png")
                    res = client.images.create_variation(
                        image=img_payload,
                        model="dall-e-2",
                        n=1,
                        size="1024x1024"
                    )
                else:
                    kwargs = {
                        "model": selected_model,
                        "prompt": full_prompt,
                        "size": api_size,
                        "n": 1
                    }
                    if "dall-e-3" in selected_model:
                        kwargs["quality"] = quality_choice

                    res = client.images.generate(**kwargs)

                if res and res.data and len(res.data) > 0:
                    generated_url = res.data[0].url

                    # نمایش تصویر
                    st.image(generated_url, caption=f"خروجی {selected_model}", use_container_width=True)

                    # ثبت در دیتابیس و کسر موجودی
                    update_balance(username, -cost)
                    log_usage(username, selected_model, "image", cost)
                    save_image_history(username, full_prompt, generated_url, selected_model, cost)

                    st.success(f"تصویر با موفقیت تولید شد! هزینه کسر شده: {int(cost):,} تومان")
                else:
                    st.error("پاسخ معتبری از موتور تصویرسازی دریافت نشد.")

        except Exception as e:
            st.error(f"خطا در ایجاد تصویر: {str(e)}")


def _render_gallery_tab(username: str):
    """نمایش آرشیو تصاویر ساخته‌شده توسط کاربر"""
    history_items = get_user_images_history(username, limit=18)
    if not history_items:
        st.info("شما هنوز تصویری با حساب کاربری خود تولید نکرده‌اید.")
        return

    st.markdown("### 🖼️ آرشیو تصاویر شما")
    cols = st.columns(3)
    for idx, item in enumerate(history_items):
        img_id, prompt, url, model, img_cost, created_at = item
        with cols[idx % 3]:
            st.markdown(f'<div class="bank-card">', unsafe_allow_html=True)
            st.image(url, use_container_width=True)
            st.caption(f"**مدل:** {model} | 📅 {created_at[:10] if created_at else ''}")
            st.markdown(f"<p style='font-size:0.8rem; color:#cbd5e1;'>{prompt[:60]}...</p>", unsafe_allow_html=True)
            st.markdown(f'<a href="{url}" target="_blank" style="text-decoration:none;"><button style="width:100%; padding:6px; border-radius:8px; background:#4f46e5; color:white; border:none; cursor:pointer;">📥 باز کردن در اندازه اصلی</button></a>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
