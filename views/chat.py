# views/chat.py
import streamlit as st
from modules.database import create_new_session, save_session_messages, update_balance, log_usage
from modules.pricing import PRICING_DB, USD_TO_TOMAN
from modules.utils import calculate_text_cost, count_message_tokens, count_string_tokens, extract_text_from_file
from modules.ui import inject_chat_scroll_script, CHAT_INPUT_PLACEHOLDER

NO_FILE_SUPPORT_MODELS = ["codex-mini-latest", "gpt-5-codex", "gpt-5-nano"]
DEFAULT_TEXT_MODEL = "gpt-4o-mini"

def render_chat_page(client, username, current_balance):
    # هدر خلاقانه
    st.markdown(
        '<div class="modern-card">'
        '<h2 style="margin:0; color:#667eea;">💬 چت هوشمند</h2>'
        '<p style="color:#718096;">دستیار هوشمند شما برای پاسخ به سوالات، تحلیل و برنامه‌نویسی</p>'
        '</div>',
        unsafe_allow_html=True,
    )

    if "active_session_id" not in st.session_state:
        st.session_state.active_session_id = None
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # --- انتخاب مدل با توضیحات ---
    c1, c2 = st.columns([3, 1])
    
    text_models = sorted([k for k, v in PRICING_DB.items() if v["type"] == "text"])
    
    # تابع برای نمایش نام + توضیحات
    def format_model_name(model_key):
        desc = PRICING_DB[model_key].get("desc", "")
        if desc:
            return f"{model_key}  (💡 {desc})"
        return model_key

    with c1:
        sel_mod = st.selectbox(
            "انتخاب مدل هوش مصنوعی",
            text_models,
            index=text_models.index(DEFAULT_TEXT_MODEL) if DEFAULT_TEXT_MODEL in text_models else 0,
            format_func=format_model_name # <--- تغییر اصلی اینجاست
        )
    
    with c2:
        m_inf = PRICING_DB[sel_mod]
        price_in = int(m_inf['input'] * USD_TO_TOMAN)
        st.info(f"💎 تعرفه ورودی:\n{price_in:,} تومان / 1M")

    # کانتینر چت
    chat_con = st.container()
    with chat_con:
        if not st.session_state.messages:
             st.markdown(
                 "<div style='text-align:center; color:#cbd5e0; margin-top:50px;'>"
                 "<h3>👋 سلام! چطور می‌تونم کمکت کنم؟</h3>"
                 "<p>سوالت رو بپرس یا فایلت رو آپلود کن.</p></div>", 
                 unsafe_allow_html=True
             )
        for m in st.session_state.messages:
            with st.chat_message(m["role"]):
                st.markdown(m["content"])

    inject_chat_scroll_script()

    # آپلود فایل
    with st.expander("📎 پیوست فایل (PDF/Word/Txt)"):
        up_f = st.file_uploader(
            "انتخاب فایل", type=["pdf", "docx", "txt"], label_visibility="collapsed",
            disabled=(sel_mod in NO_FILE_SUPPORT_MODELS)
        )
        f_txt = ""
        if up_f:
            t, e = extract_text_from_file(up_f)
            if not e:
                f_txt = f"\n📎 FILE: {up_f.name}\n{t}\n"
                st.success(f"فایل {up_f.name} خوانده شد.")
            else:
                st.error(e)

    # ورودی پیام
    if prompt := st.chat_input(CHAT_INPUT_PLACEHOLDER):
        if current_balance < 50:
            st.error("شارژ کیف پول شما کافی نیست.")
        else:
            if not st.session_state.active_session_id:
                st.session_state.active_session_id = create_new_session(username, prompt)
            
            full_msg = prompt + f_txt
            st.session_state.messages.append({"role": "user", "content": full_msg})
            save_session_messages(st.session_state.active_session_id, st.session_state.messages)

            with chat_con:
                with st.chat_message("user"):
                    st.markdown(prompt)

            with chat_con:
                with st.chat_message("assistant"):
                    try:
                        ph = st.empty()
                        full_resp = ""
                        
                        # آماده‌سازی پیام‌ها
                        msgs = list(st.session_state.messages)
                        # سیستم پرامپت ساده
                        if "o1" not in sel_mod:
                            msgs.insert(0, {"role": "system", "content": "You are a helpful Persian assistant."})

                        stream = client.chat.completions.create(
                            model=sel_mod, messages=msgs, stream=True,
                            temperature=0.7 if "o1" not in sel_mod else 1
                        )

                        for chunk in stream:
                            if chunk.choices and chunk.choices[0].delta.content:
                                full_resp += chunk.choices[0].delta.content
                                ph.markdown(full_resp + "▌")

                        ph.markdown(full_resp)

                        st.session_state.messages.append({"role": "assistant", "content": full_resp})
                        save_session_messages(st.session_state.active_session_id, st.session_state.messages)

                        # محاسبه هزینه
                        inp_tok = count_message_tokens(msgs, sel_mod)
                        out_tok = count_string_tokens(full_resp, sel_mod)
                        cost = calculate_text_cost(sel_mod, inp_tok, out_tok)

                        update_balance(username, -cost)
                        log_usage(username, sel_mod, "chat", cost)

                    except Exception as e:
                        st.error(f"خطا: {e}")