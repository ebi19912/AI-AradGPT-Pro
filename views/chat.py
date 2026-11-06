# views/chat.py
"""
ویوی چت هوشمند (Smart Chat Studio)
پشتیبانی از مدل‌های OpenRouter, GapGPT, OpenAI, Claude, DeepSeek و مدل‌های سفارشی
با امکان استریم پاسخ، پیوست اسناد (PDF/Word/TXT)، قالب‌های پرامپت آماده، و مدیریت سشن‌ها
"""

import streamlit as st
from typing import List, Dict, Any
from modules.database import (
    create_new_session,
    save_session_messages,
    update_balance,
    log_usage,
    rename_session
)
from modules.pricing import (
    PRICING_DB,
    get_usd_to_toman,
    calculate_text_cost,
    get_model_info
)
from modules.utils import (
    count_message_tokens,
    count_string_tokens,
    extract_text_from_file
)
from modules.ui import inject_chat_scroll_script, CHAT_INPUT_PLACEHOLDER
from modules.config import get_active_provider_key, PROVIDERS

# قالب‌های پرامپت آماده
PROMPT_TEMPLATES = {
    "💻 دستیار برنامه‌نویسی": "لطفاً به عنوان یک معمار ارشد نرم‌افزار، کدهای زیر را بررسی، بهینه‌سازی و خطایابی کن. توضیحات را دقیق و گام‌به‌گام به همراه مثال بنویس:\n\n",
    "✍️ نویسنده محتوا": "یک مقاله جذاب، حرفه‌ای و بهینه‌شده برای سئو در مورد موضوع زیر با لحنی روان و تاثیرگذار بنویس:\n\n",
    "🌐 ترجمه و ویراستاری": "متن زیر را با حفظ لحن و اصطلاحات تخصصی، به فارسی بسیار سلیس و شایسته ترجمه و ویراستاری کن:\n\n",
    "📊 خلاصه‌ساز و تحلیلگر": "متن یا سند زیر را به صورت نکات کلیدی (Bullet Points) خلاصه کن و مهم‌ترین بینش‌ها و نتایج آن را برجسته ساز:\n\n"
}


def render_chat_page(client, username: str, current_balance: float):
    st.markdown(
        '<div class="modern-card">'
        '<h2 style="margin:0; color:#a5b4fc;">💬 استودیو چت هوشمند</h2>'
        '<p style="color:#94a3b8; margin:4px 0 0 0;">پشتیبانی از برترین مدل‌های هوش مصنوعی جهان با تحلیل عمیق و پاسخ فوری</p>'
        '</div>',
        unsafe_allow_html=True,
    )

    if "active_session_id" not in st.session_state:
        st.session_state.active_session_id = None
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "chat_system_prompt" not in st.session_state:
        st.session_state.chat_system_prompt = "You are AradGPT Pro, an expert, thoughtful, and highly capable Persian and English AI assistant."
    if "chat_temperature" not in st.session_state:
        st.session_state.chat_temperature = 0.7

    # --- انتخاب مدل و ارائه‌دهنده ---
    prov_key = get_active_provider_key()
    prov_data = PROVIDERS.get(prov_key, {})
    default_prov_models = prov_data.get("default_models", [])

    # تجمیع مدل‌های متنی شناخته شده
    known_text_models = [k for k, v in PRICING_DB.items() if v.get("type") == "text"]
    all_available_models = []
    
    # مدل‌های ارائه‌دهنده جاری در اولویت
    for m in default_prov_models:
        if m not in all_available_models:
            all_available_models.append(m)
    for m in known_text_models:
        if m not in all_available_models:
            all_available_models.append(m)

    all_available_models.append("➕ مدل سفارشی (تایپ دستی...)")

    def format_model_label(key: str) -> str:
        if key.startswith("➕"):
            return key
        info = get_model_info(key)
        desc = info.get("desc", "")
        return f"{key}  —  ({desc})" if desc else key

    col_model, col_tariff = st.columns([3, 1])

    with col_model:
        selected_option = st.selectbox(
            "انتخاب مدل هوش مصنوعی",
            all_available_models,
            index=0,
            format_func=format_model_label
        )

        if selected_option.startswith("➕"):
            chosen_model = st.text_input("نام شناسه مدل را وارد کنید (مثال: openrouter/free, mistral/mistral-large)", value="openai/gpt-4o-mini")
        else:
            chosen_model = selected_option

    with col_tariff:
        m_info = get_model_info(chosen_model)
        usd_rate = get_usd_to_toman()
        in_toman = int(m_info.get("input", 1.0) * usd_rate)
        out_toman = int(m_info.get("output", 3.0) * usd_rate)
        st.markdown(
            f"""
            <div style="background:rgba(255,255,255,0.03); border:1px solid rgba(255,255,255,0.08); border-radius:12px; padding:8px 12px; text-align:center;">
                <span style="font-size:0.8rem; color:#94a3b8;">💎 تعرفه هر ۱ میلیون توکن:</span><br>
                <b style="color:#10b981; font-size:0.85rem;">ورودی: {in_toman:,} ت</b> | 
                <b style="color:#60a5fa; font-size:0.85rem;">خروجی: {out_toman:,} ت</b>
            </div>
            """,
            unsafe_allow_html=True
        )

    # --- تنظیمات پیشرفته چت (Accordion) ---
    with st.expander("⚙️ تنظیمات پیشرفته گفتگو (پرامپت سیستمی، دمای پاسخ و خروجی)"):
        c_set1, c_set2 = st.columns([2, 1])
        with c_set1:
            st.session_state.chat_system_prompt = st.text_area(
                "دستورالعمل سیستمی (System Prompt)",
                value=st.session_state.chat_system_prompt,
                height=80,
                help="نقش و رفتار هوش مصنوعی را برای این گفتگو مشخص کنید."
            )
        with c_set2:
            st.session_state.chat_temperature = st.slider(
                "میزان خلاقیت (Temperature)",
                min_value=0.0,
                max_value=1.5,
                value=st.session_state.chat_temperature,
                step=0.1,
                help="مقادیر کمتر برای کارهای منطقی/کد و مقادیر بیشتر برای پاسخ‌های خلاقانه."
            )

        # دکمه‌های پرامپت آماده
        st.markdown("<p style='font-size:0.85rem; color:#94a3b8; margin-bottom:6px;'>💡 قالب‌های آماده برای پرامپت:</p>", unsafe_allow_html=True)
        t_cols = st.columns(len(PROMPT_TEMPLATES))
        for idx, (t_name, t_text) in enumerate(PROMPT_TEMPLATES.items()):
            with t_cols[idx]:
                if st.button(t_name, key=f"tpl_{idx}", use_container_width=True):
                    st.session_state.preset_prompt = t_text

    # --- مدیریت سشن جاری (تغییر نام، پاکسازی، دانلود) ---
    if st.session_state.messages:
        c_act1, c_act2, c_act3 = st.columns([2, 1, 1])
        with c_act1:
            if st.session_state.active_session_id:
                new_title_input = st.text_input("تغییر عنوان گفتگو:", value="", placeholder="عنوان جدید گفتگو...", label_visibility="collapsed")
                if st.button("ذخیره عنوان جدید") and new_title_input:
                    rename_session(st.session_state.active_session_id, new_title_input)
                    st.toast("عنوان گفتگو بروزرسانی شد.")
                    st.rerun()
        with c_act2:
            # خروجی گرفتن از گفتگو
            full_chat_text = "\n\n".join([f"**{m['role'].upper()}**:\n{m['content']}" for m in st.session_state.messages])
            st.download_button(
                "📥 دریافت گفت‌وگو (.md)",
                data=full_chat_text,
                file_name=f"aradgpt_chat_{username}.md",
                mime="text/markdown",
                use_container_width=True
            )
        with c_act3:
            if st.button("🗑️ پاک کردن گفتگو", use_container_width=True):
                st.session_state.messages = []
                if st.session_state.active_session_id:
                    save_session_messages(st.session_state.active_session_id, [])
                st.rerun()

    # --- کانتینر نمایش پیام‌ها ---
    chat_con = st.container()
    with chat_con:
        if not st.session_state.messages:
            st.markdown(
                """
                <div style="text-align:center; padding: 40px 20px; color:#64748b;">
                    <div style="font-size:3rem; margin-bottom:10px;">✨</div>
                    <h3 style="color:#cbd5e1; margin-bottom:8px;">سلام! چه کمکی از دست من برمی‌آید؟</h3>
                    <p style="font-size:0.95rem;">سوال خود را بپرسید، متنی برای تحلیل بفرستید یا فایلی را پیوست نمایید.</p>
                </div>
                """,
                unsafe_allow_html=True
            )
        for msg in st.session_state.messages:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])

    inject_chat_scroll_script()

    # --- بخش پیوست اسناد ---
    file_context = ""
    with st.expander("📎 پیوست سند یا فایل برای تحلیل (PDF, Word, TXT, CSV, Code)"):
        uploaded_file = st.file_uploader(
            "انتخاب سند",
            type=["pdf", "docx", "txt", "csv", "json", "md", "py"],
            label_visibility="collapsed"
        )
        if uploaded_file:
            extracted_text, err = extract_text_from_file(uploaded_file)
            if err:
                st.error(err)
            else:
                tok_estimate = count_string_tokens(extracted_text, chosen_model)
                st.success(f"فایل «{uploaded_file.name}» خوانده شد. (تقریباً {tok_estimate:,} توکن)")
                file_context = f"\n\n--- [پیوست سند: {uploaded_file.name}] ---\n{extracted_text}\n--- [پایان سند] ---\n"

    # پرکردن پرامپت آماده در صورت کلیک
    default_input_val = st.session_state.pop("preset_prompt", "")
    if default_input_val:
        st.info("💡 قالب پرامپت در کادر ورودی اعمال شد؛ می‌توانید متن خود را به انتهای آن اضافه کنید.")

    # --- ورودی چت ---
    if prompt := st.chat_input(CHAT_INPUT_PLACEHOLDER):
        if current_balance < 20:
            st.error("موجودی کیف پول شما کافی نیست. لطفاً حساب خود را شارژ فرمایید.")
            return

        if not client:
            st.error("ارتباط با سرویس هوش مصنوعی برقرار نیست. لطفاً تنظیمات API را بررسی کنید.")
            return

        if not st.session_state.active_session_id:
            st.session_state.active_session_id = create_new_session(username, prompt)

        full_user_content = prompt + file_context
        st.session_state.messages.append({"role": "user", "content": full_user_content})
        save_session_messages(st.session_state.active_session_id, st.session_state.messages)

        with chat_con:
            with st.chat_message("user"):
                st.markdown(prompt)
                if file_context:
                    st.caption(f"📎 سند ضمیمه ارسال شد.")

        # پاسخ مدل هوش مصنوعی
        with chat_con:
            with st.chat_message("assistant"):
                response_box = st.empty()
                full_assistant_reply = ""

                # آماده‌سازی پیام‌ها برای ارسال به API
                api_messages = []
                if st.session_state.chat_system_prompt and "o1" not in chosen_model:
                    api_messages.append({"role": "system", "content": st.session_state.chat_system_prompt})

                for m in st.session_state.messages:
                    api_messages.append({"role": m["role"], "content": m["content"]})

                try:
                    kwargs = {
                        "model": chosen_model,
                        "messages": api_messages,
                        "stream": True
                    }
                    if "o1" not in chosen_model and "o3" not in chosen_model:
                        kwargs["temperature"] = float(st.session_state.chat_temperature)

                    stream = client.chat.completions.create(**kwargs)

                    for chunk in stream:
                        if chunk.choices and chunk.choices[0].delta and chunk.choices[0].delta.content:
                            full_assistant_reply += chunk.choices[0].delta.content
                            response_box.markdown(full_assistant_reply + " ▌")

                    response_box.markdown(full_assistant_reply)

                    # ذخیره در تاریخچه
                    st.session_state.messages.append({"role": "assistant", "content": full_assistant_reply})
                    save_session_messages(st.session_state.active_session_id, st.session_state.messages)

                    # محاسبه هزینه و کسر موجودی
                    in_tokens = count_message_tokens(api_messages, chosen_model)
                    out_tokens = count_string_tokens(full_assistant_reply, chosen_model)
                    cost = calculate_text_cost(chosen_model, in_tokens, out_tokens)

                    update_balance(username, -cost)
                    log_usage(username, chosen_model, "chat", cost)

                    st.toast(f"مصرف: {in_tokens + out_tokens:,} توکن | هزینه: {int(cost)} تومان")
                    st.rerun()

                except Exception as ex:
                    error_str = str(ex)
                    response_box.error(f"خطا در دریافت پاسخ: {error_str}")
