import streamlit as st
import time
from modules.pricing import PRICING_DB, USD_TO_TOMAN
from modules.database import update_balance, log_usage

DEFAULT_AUDIO_MODEL = "gpt-4o-mini-tts"
VOICE_MAP = {
    "alloy": "🎭 Alloy (خنثی و همه‌کاره)",
    "echo": "🎪 Echo (گرم و مردانه)",
    "fable": "📚 Fable (لحن داستانی)",
    "onyx": "🎯 Onyx (بم و مقتدر)",
    "nova": "⚡ Nova (پرانرژی و زنانه)",
    "shimmer": "✨ Shimmer (آرام و شفاف)",
}

def render_audio_page(client, username, current_balance):
    st.markdown(
        '<div class="modern-card"><h2 style="margin:0; color:#667eea;">🎹 استودیو صوتی</h2>'
        '<p style="color:#666;">جعبه ابزار کامل هوش مصنوعی صوتی</p></div>',
        unsafe_allow_html=True,
    )

    tab_tts, tab_stt = st.tabs(["🎙️ تبدیل متن به صدا (TTS)", "🎧 تبدیل صوت به متن (STT)"])

    with tab_tts:
        _render_tts_content(client, username, current_balance)

    with tab_stt:
        _render_stt_content(client, username, current_balance)

# --- Helper Function for Formatting ---
def format_audio_model(model_key):
    desc = PRICING_DB.get(model_key, {}).get("desc", "")
    if desc:
        return f"{model_key} (🎵 {desc})"
    return model_key

def _render_tts_content(client, username, current_balance):
    c1, c2 = st.columns([3, 1])
    with c1:
        aud_models = sorted([k for k, v in PRICING_DB.items() if v.get("type") == "audio"])
        idx = aud_models.index(DEFAULT_AUDIO_MODEL) if DEFAULT_AUDIO_MODEL in aud_models else 0
        
        mod = st.selectbox(
            "موتور تبدیل صدا", 
            aud_models, 
            index=idx, 
            key="tts_model",
            format_func=format_audio_model # <--- توضیحات اضافه شد
        )
    
    with c2:
        price = int(PRICING_DB[mod]["price"] * USD_TO_TOMAN)
        st.info(f"💎 تعرفه:\n{price:,} تومان / 1M")

    voice_key = st.selectbox("انتخاب گوینده", list(VOICE_MAP.keys()), format_func=lambda x: VOICE_MAP[x])
    txt = st.text_area("متن را وارد کنید...", height=120, placeholder="سلام، من هوش مصنوعی هستم...")

    if st.button("تولید صدا 🎵", type="primary", use_container_width=True):
        if not txt:
            st.warning("متن خالی است!")
            return
        
        cost = (len(txt) / 1e6) * PRICING_DB[mod]["price"] * USD_TO_TOMAN
        if current_balance < cost:
            st.error(f"موجودی ناکافی. هزینه: {int(cost)} تومان")
            return

        try:
            with st.spinner("در حال ضبط..."):
                res = client.audio.speech.create(model=mod, voice=voice_key, input=txt)
                st.audio(res.content, format="audio/mp3")
                
                update_balance(username, -cost)
                log_usage(username, mod, "audio", cost)
                st.success(f"انجام شد! هزینه: {int(cost)} تومان")
        except Exception as e:
            st.error(f"خطا: {e}")


def _render_stt_content(client, username, current_balance):
    c1, c2 = st.columns([3, 1])
    with c1:
        stt_models = sorted([k for k, v in PRICING_DB.items() if v.get("type") == "stt"])
        mod = st.selectbox(
            "موتور پردازش", 
            stt_models, 
            index=0, 
            key="stt_model",
            format_func=format_audio_model # <--- توضیحات اضافه شد
        )
    with c2:
        price = int(PRICING_DB[mod]["price"] * USD_TO_TOMAN)
        st.info(f"💎 تعرفه:\n{price:,} تومان / 1M")

    mode = st.radio("روش ورودی", ["آپلود فایل", "ضبط صدا"], horizontal=True, label_visibility="collapsed")
    
    audio_file = None
    if mode == "آپلود فایل":
        audio_file = st.file_uploader("فایل صوتی (MP3/WAV)", type=["mp3", "wav", "ogg"])
    else:
        audio_file = st.audio_input("ضبط کنید")

    if st.button("شروع تبدیل 📝", key="btn_stt", use_container_width=True) and audio_file:
        if current_balance < 500:
            st.error("موجودی ناکافی.")
            return

        try:
            with st.spinner("در حال نوشتن..."):
                api_mod = mod.replace("gapgpt/", "")
                res = client.audio.transcriptions.create(model=api_mod, file=audio_file)
                
                st.text_area("خروجی متن:", res.text, height=200)
                
                cost = max(50, (len(res.text)/4/1e6) * PRICING_DB[mod]["price"] * USD_TO_TOMAN)
                update_balance(username, -cost)
                log_usage(username, mod, "stt", cost)
                st.toast(f"هزینه: {int(cost)} تومان")
        except Exception as e:
            st.error(f"خطا: {e}")