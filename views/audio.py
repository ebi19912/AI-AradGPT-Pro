# views/audio.py
"""
استودیو صوتی (Audio Studio)
تبدیل متن به گفتار طبیعی (TTS) و پیاده‌سازی صوت به متن با هوش مصنوعی Whisper (STT)
"""

import streamlit as st
from modules.pricing import PRICING_DB, get_usd_to_toman, calculate_audio_tts_cost, calculate_audio_stt_cost
from modules.database import update_balance, log_usage
from modules.config import get_active_provider_key, PROVIDERS

DEFAULT_AUDIO_MODEL = "tts-1"
VOICE_MAP = {
    "alloy": "🎭 Alloy (متعادل و شفاف)",
    "echo": "🎪 Echo (گرم و مردانه)",
    "fable": "📚 Fable (لحن روایی و داستانی)",
    "onyx": "🎯 Onyx (بم، عمیق و جدی)",
    "nova": "⚡ Nova (پرانرژی و زنانه)",
    "shimmer": "✨ Shimmer (آرام، ملایم و کریستالی)",
}


def render_audio_page(client, username: str, current_balance: float):
    st.markdown(
        '<div class="modern-card">'
        '<h2 style="margin:0; color:#a5b4fc;">🎙️ استودیو صوتی هوشمند</h2>'
        '<p style="color:#94a3b8; margin:4px 0 0 0;">تبدیل هوشمندانه متن به گفتار و پیاده‌سازی خودکار صوت به متن با دقت بالا</p>'
        '</div>',
        unsafe_allow_html=True,
    )

    prov_key = get_active_provider_key()
    prov_info = PROVIDERS.get(prov_key, {})
    if not prov_info.get("supports_audio", False) and "openrouter" in prov_key:
        st.warning(
            "⚠️ ارائه‌دهنده فعال سیستم شما در حال حاضر **OpenRouter** است که عمدتاً متمرکز بر مدل‌های زبانی متنی می‌باشد. "
            "برای پردازش‌های صوتی (TTS و Whisper) توصیه می‌شود در پنل مدیریت از ارائه‌دهنده **GapGPT**، **OpenAI** یا **Groq** استفاده فرمایید."
        )

    tab_tts, tab_stt = st.tabs(["🎙️ تبدیل متن به صدا (TTS)", "🎧 پیاده‌سازی صوت به متن (STT)"])

    with tab_tts:
        _render_tts_content(client, username, current_balance)

    with tab_stt:
        _render_stt_content(client, username, current_balance)


def _render_tts_content(client, username: str, current_balance: float):
    aud_models = sorted([k for k, v in PRICING_DB.items() if v.get("type") == "audio"])
    if not aud_models:
        aud_models = ["tts-1", "tts-1-hd", "gpt-4o-mini-tts"]

    c1, c2 = st.columns([3, 1])
    with c1:
        mod = st.selectbox(
            "موتور تبدیل صدا",
            aud_models,
            index=aud_models.index(DEFAULT_AUDIO_MODEL) if DEFAULT_AUDIO_MODEL in aud_models else 0,
            key="tts_model"
        )

    with c2:
        usd_rate = get_usd_to_toman()
        unit_price = int(PRICING_DB.get(mod, {}).get("price", 15.0) * usd_rate)
        st.markdown(
            f"""
            <div style="background:rgba(255,255,255,0.03); border:1px solid rgba(255,255,255,0.08); border-radius:12px; padding:10px; text-align:center;">
                <span style="font-size:0.8rem; color:#94a3b8;">💎 تعرفه هر ۱ میلیون کاراکتر:</span><br>
                <b style="color:#10b981; font-size:1.05rem;">{unit_price:,} تومان</b>
            </div>
            """,
            unsafe_allow_html=True
        )

    col_voice, col_speed = st.columns([2, 1])
    with col_voice:
        voice_key = st.selectbox("انتخاب لحن و گوینده", list(VOICE_MAP.keys()), format_func=lambda x: VOICE_MAP[x])
    with col_speed:
        speed_val = st.slider("سرعت خوانش (Speed)", min_value=0.5, max_value=2.0, value=1.0, step=0.1)

    txt = st.text_area(
        "متن مورد نظر برای گویندگی را وارد فرمایید...",
        height=130,
        placeholder="سلام و درود! به سامانه هوش مصنوعی AradGPT Pro خوش آمدید..."
    )

    if st.button("🎵 تولید فایل صوتی", type="primary", use_container_width=True):
        if not txt.strip():
            st.warning("لطفاً ابتدا متنی را برای تبدیل به صوت بنویسید.")
            return

        cost = calculate_audio_tts_cost(mod, len(txt))
        if current_balance < cost:
            st.error(f"موجودی کیف پول شما کافی نیست. هزینه برآورد شده: {int(cost):,} تومان")
            return

        if not client:
            st.error("کلاینت هوش مصنوعی متصل نیست.")
            return

        try:
            with st.spinner("در حال سنتز و تولید صوت طبیعی..."):
                response = client.audio.speech.create(
                    model=mod,
                    voice=voice_key,
                    input=txt.strip(),
                    speed=speed_val
                )

                audio_bytes = response.content
                st.audio(audio_bytes, format="audio/mp3")

                # دکمه دانلود مستقیم
                st.download_button(
                    "📥 دانلود فایل صوتی (.mp3)",
                    data=audio_bytes,
                    file_name=f"aradgpt_speech_{voice_key}.mp3",
                    mime="audio/mp3",
                    use_container_width=True
                )

                update_balance(username, -cost)
                log_usage(username, mod, "audio_tts", cost)
                st.success(f"صوت با موفقیت ایجاد شد! هزینه: {int(cost)} تومان")

        except Exception as e:
            st.error(f"خطا در تولید صوت: {str(e)}")


def _render_stt_content(client, username: str, current_balance: float):
    stt_models = sorted([k for k, v in PRICING_DB.items() if v.get("type") == "stt"])
    if not stt_models:
        stt_models = ["whisper-1", "gapgpt/whisper-1"]

    c1, c2 = st.columns([3, 1])
    with c1:
        mod = st.selectbox("موتور تبدیل صوت به متن (Speech-to-Text)", stt_models, index=0, key="stt_model")

    with c2:
        usd_rate = get_usd_to_toman()
        rate_toman = int(PRICING_DB.get(mod, {}).get("price", 10.0) * usd_rate)
        st.markdown(
            f"""
            <div style="background:rgba(255,255,255,0.03); border:1px solid rgba(255,255,255,0.08); border-radius:12px; padding:10px; text-align:center;">
                <span style="font-size:0.8rem; color:#94a3b8;">💎 تعرفه:</span><br>
                <b style="color:#60a5fa; font-size:1.05rem;">{rate_toman:,} تومان</b>
            </div>
            """,
            unsafe_allow_html=True
        )

    col_lang, col_mode = st.columns([1, 2])
    with col_lang:
        lang_choice = st.selectbox("زبان گفتار", ["تشخیص خودکار", "fa (فارسی)", "en (انگلیسی)"], index=0)
    with col_mode:
        mode = st.radio("روش دریافت صدا", ["آپلود فایل صوتی", "ضبط زنده صدا از میکروفون"], horizontal=True)

    audio_file = None
    if mode.startswith("آپلود"):
        audio_file = st.file_uploader("انتخاب فایل صوتی", type=["mp3", "wav", "ogg", "m4a", "webm"])
    else:
        audio_file = st.audio_input("میکروفون را فعال کرده و صحبت کنید")

    if st.button("📝 شروع استخراج و پیاده‌سازی متن", key="btn_run_stt", type="primary", use_container_width=True):
        if not audio_file:
            st.warning("لطفاً یک فایل صوتی آپلود کنید یا صدایی ضبط فرمایید.")
            return

        if current_balance < 100:
            st.error("حداقل موجودی ۱۰۰ تومان برای پیاده‌سازی صوت نیاز است.")
            return

        if not client:
            st.error("کلاینت هوش مصنوعی متصل نیست.")
            return

        try:
            with st.spinner("هوش مصنوعی در حال تحلیل صوت و پیاده‌سازی متن است..."):
                pure_mod = mod.replace("gapgpt/", "")
                # بسته‌بندی فایل برای سازگاری کامل با کتابخانه openai
                file_tuple = (audio_file.name or "audio.wav", audio_file.getvalue(), audio_file.type or "audio/wav")

                kwargs = {
                    "model": pure_mod,
                    "file": file_tuple
                }
                if "fa" in lang_choice:
                    kwargs["language"] = "fa"
                elif "en" in lang_choice:
                    kwargs["language"] = "en"

                transcript_obj = client.audio.transcriptions.create(**kwargs)
                extracted_text = transcript_obj.text

                st.markdown("### 📄 متن پیاده‌سازی شده:")
                st.text_area("خروجی کامل", value=extracted_text, height=180, label_visibility="collapsed")

                st.download_button(
                    "📥 دانلود خروجی متن (.txt)",
                    data=extracted_text,
                    file_name="transcript.txt",
                    mime="text/plain",
                    use_container_width=True
                )

                cost = calculate_audio_stt_cost(mod, len(extracted_text))
                update_balance(username, -cost)
                log_usage(username, mod, "audio_stt", cost)
                st.success(f"عملیات انجام شد! هزینه کسر شده: {int(cost)} تومان")

        except Exception as e:
            st.error(f"خطا در پیاده‌سازی متن: {str(e)}")
