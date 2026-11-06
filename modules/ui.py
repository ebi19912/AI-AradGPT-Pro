# modules/ui.py
"""
ماژول رابط کاربری مدرن (Glassmorphic Dark Theme) با پشتیبانی کامل از زبان فارسی،
RTL پیشرفته، فونت‌های بومی، دکمه‌های شناور هوشمند و ویجت‌های تعاملی
"""

import base64
import os
import json
import streamlit as st
import streamlit.components.v1 as components

CHAT_INPUT_PLACEHOLDER = "پیام خود را به زبان فارسی یا انگلیسی بنویسید..."


def _load_font(font_name: str, file_name: str) -> str:
    """بارگذاری فونت از پوشه محلی fonts و تبدیل به Base64"""
    font_path = os.path.join("fonts", file_name)
    if os.path.exists(font_path):
        try:
            with open(font_path, "rb") as f:
                data = f.read()
                return base64.b64encode(data).decode()
        except Exception:
            pass
    return ""


def load_advanced_css() -> str:
    """تولید استایل‌های CSS پیشرفته تم دارک و شیشه‌ای (Qwen / DeepSeek Style)"""
    vazir_b64 = _load_font("Vazirmatn", "Vazir.ttf")
    shabnam_b64 = _load_font("Shabnam", "Shabnam.ttf")

    font_faces = []
    if vazir_b64:
        font_faces.append(f"""
        @font-face {{
            font-family: 'Vazirmatn';
            src: url('data:font/ttf;base64,{vazir_b64}') format('truetype');
            font-weight: 300 700;
            font-display: swap;
        }}
        """)
    if shabnam_b64:
        font_faces.append(f"""
        @font-face {{
            font-family: 'Shabnam';
            src: url('data:font/ttf;base64,{shabnam_b64}') format('truetype');
            font-weight: normal;
            font-display: swap;
        }}
        """)

    custom_fonts = "\n".join(font_faces)

    return f"""
    <style>
    /* === 1. فونت‌های وب و محلی === */
    @import url('https://fonts.googleapis.com/css2?family=Vazirmatn:wght@300;400;500;600;700;800&family=Fira+Code:wght@400;500&display=swap');
    {custom_fonts}

    /* === 2. متغیرهای رنگی تم شیشه‌ای مدرن === */
    :root {{
        --bg-main: #0b0f19;
        --sidebar-bg: linear-gradient(180deg, #0d1322 0%, #080c16 100%);
        --primary-gradient: linear-gradient(135deg, #6366f1 0%, #8b5cf6 50%, #d946ef 100%);
        --accent-emerald: linear-gradient(135deg, #10b981 0%, #059669 100%);
        --card-bg: rgba(17, 24, 39, 0.75);
        --card-border: rgba(255, 255, 255, 0.08);
        --glass-hover: rgba(255, 255, 255, 0.05);
        --text-primary: #f8fafc;
        --text-secondary: #94a3b8;
        --text-muted: #64748b;
    }}

    /* اعمال فونت فارسی به تمامی المان‌ها */
    html, body, [class*="css"], p, div, span, label, input, button, select, textarea {{
        font-family: 'Vazirmatn', 'Shabnam', system-ui, -apple-system, sans-serif !important;
    }}

    /* جهت‌گیری راست‌به‌چپ سراسری برای متون */
    .stMarkdown, .stSelectbox, .stTextInput, .stTextArea, .stForm, .stChatMessage {{
        direction: rtl;
        text-align: right;
    }}

    /* محتوای انگلیسی و کدها LTR */
    code, pre, .stCodeBlock, .stJson, .stDataFrame, .ltr-text, [data-testid="stCodeBlock"] {{
        direction: ltr !important;
        text-align: left !important;
        font-family: 'Fira Code', Consolas, Monaco, monospace !important;
    }}

    /* === 3. سایدبار حرفه‌ای === */
    [data-testid="stSidebar"] {{
        background: var(--sidebar-bg);
        border-left: 1px solid var(--card-border);
        box-shadow: -4px 0 25px rgba(0, 0, 0, 0.3);
    }}

    [data-testid="stSidebar"] > div:first-child {{
        padding-top: 1.5rem;
    }}

    /* کارت پروفایل کاربر در سایدبار */
    .user-profile-box {{
        background: rgba(255, 255, 255, 0.03);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 18px;
        padding: 16px 14px;
        margin: 10px 0 20px 0;
        text-align: center;
        backdrop-filter: blur(12px);
        position: relative;
        overflow: hidden;
    }}
    .user-profile-box::before {{
        content: "";
        position: absolute;
        top: 0; left: 0; right: 0;
        height: 3px;
        background: var(--primary-gradient);
    }}
    .user-profile-box h3 {{
        color: #f1f5f9 !important;
        margin: 0 0 6px 0;
        font-size: 1.05rem;
        font-weight: 600;
    }}
    .user-profile-box p {{
        background: var(--primary-gradient);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        margin: 0;
        font-weight: 700;
        font-size: 1.15rem;
    }}

    /* رادیو دکمه‌های ناوبری اصلی */
    .stRadio > div[role="radiogroup"] {{
        gap: 8px;
    }}
    .stRadio div[role="radiogroup"] label > div:first-child {{
        display: none !important;
    }}
    .stRadio > div[role="radiogroup"] label {{
        background: rgba(255, 255, 255, 0.02);
        border: 1px solid transparent;
        border-radius: 12px;
        padding: 10px 14px;
        color: var(--text-secondary) !important;
        cursor: pointer;
        transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
        display: flex;
        align-items: center;
        gap: 10px;
        width: 100%;
    }}
    .stRadio > div[role="radiogroup"] label:hover {{
        background: var(--glass-hover);
        color: #ffffff !important;
        transform: translateX(-4px);
        border-color: rgba(99, 102, 241, 0.3);
    }}
    .stRadio > div[role="radiogroup"] label[data-checked="true"] {{
        background: rgba(99, 102, 241, 0.15) !important;
        border-right: 3px solid #8b5cf6 !important;
        border-color: rgba(139, 92, 246, 0.4);
    }}
    .stRadio > div[role="radiogroup"] label[data-checked="true"] p {{
        color: #ffffff !important;
        font-weight: 600 !important;
    }}

    /* === 4. کارت‌های شیشه‌ای محتوا (Glass Cards) === */
    .modern-card {{
        background: var(--card-bg);
        border: 1px solid var(--card-border);
        border-radius: 20px;
        padding: 24px 28px;
        margin-bottom: 20px;
        backdrop-filter: blur(16px);
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.25);
        position: relative;
        overflow: hidden;
    }}
    .modern-card::before {{
        content: "";
        position: absolute;
        top: 0; right: 0;
        width: 4px;
        height: 100%;
        background: var(--primary-gradient);
    }}

    /* کارت موجودی کیف پول */
    .wallet-card {{
        background: linear-gradient(135deg, rgba(99, 102, 241, 0.15) 0%, rgba(139, 92, 246, 0.1) 100%);
        border: 1px solid rgba(139, 92, 246, 0.3);
        border-radius: 20px;
        padding: 28px;
        margin-bottom: 22px;
        text-align: center;
        backdrop-filter: blur(15px);
    }}
    .wallet-card h2 {{
        margin: 0;
        color: var(--text-secondary);
        font-size: 1rem;
        font-weight: 400;
    }}
    .wallet-card h1 {{
        margin: 10px 0;
        color: #ffffff;
        font-size: 2.2rem;
        font-weight: 800;
        background: var(--primary-gradient);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }}

    /* کارت حساب بانکی */
    .bank-card {{
        background: rgba(255, 255, 255, 0.03);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 14px;
        padding: 16px;
        margin-bottom: 12px;
        transition: transform 0.2s ease;
    }}
    .bank-card:hover {{
        transform: translateY(-2px);
        border-color: rgba(99, 102, 241, 0.4);
    }}

    /* نشان‌های وضعیت (Badges) */
    .badge-pending {{
        background: rgba(245, 158, 11, 0.2);
        color: #fbbf24;
        padding: 4px 10px;
        border-radius: 20px;
        font-size: 0.85rem;
        font-weight: 600;
    }}
    .badge-approved {{
        background: rgba(16, 185, 129, 0.2);
        color: #34d399;
        padding: 4px 10px;
        border-radius: 20px;
        font-size: 0.85rem;
        font-weight: 600;
    }}
    .badge-rejected {{
        background: rgba(239, 68, 68, 0.2);
        color: #f87171;
        padding: 4px 10px;
        border-radius: 20px;
        font-size: 0.85rem;
        font-weight: 600;
    }}

    /* استایل دکمه‌ها */
    .stButton > button {{
        border-radius: 12px !important;
        font-weight: 500 !important;
        transition: all 0.2s ease !important;
    }}
    .stButton > button:hover {{
        transform: translateY(-1px);
    }}

    /* تب‌ها */
    .stTabs [data-baseweb="tab-list"] {{
        gap: 8px;
        border-bottom: 1px solid var(--card-border);
        padding-bottom: 8px;
    }}
    .stTabs [data-baseweb="tab"] {{
        border-radius: 10px !important;
        padding: 8px 16px !important;
        color: var(--text-secondary) !important;
    }}
    .stTabs [aria-selected="true"] {{
        background: rgba(99, 102, 241, 0.15) !important;
        color: #ffffff !important;
        border-bottom: 2px solid #8b5cf6 !important;
    }}

    /* فیلدهای ورودی */
    .stTextInput input, .stTextArea textarea, .stSelectbox select {{
        border-radius: 12px !important;
    }}

    /* چت حباب‌ها */
    [data-testid="stChatMessage"] {{
        border-radius: 16px;
        padding: 16px 20px;
        margin-bottom: 12px;
        backdrop-filter: blur(8px);
    }}

    /* مخفی‌سازی هدر استاندارد استریم‌لیت */
    header, footer, .stAppDeployButton {{
        display: none !important;
    }}
    </style>
    """


def inject_copy_button_script():
    """تزریق جاوااسکریپت برای فعال‌سازی کپی‌کردن بلوک‌های کد"""
    script = """<script>
    (function(){
        const doc = window.parent.document;
        const obs = new MutationObserver(() => {
            doc.querySelectorAll('[data-testid="stCopyToClipboard"]').forEach(b => {
                if(!b.classList.contains('p')){ b.classList.add('p'); }
            });
        });
        obs.observe(doc.body, {childList: true, subtree: true});
    })();
    </script>"""
    components.html(script, height=0, width=0)


def inject_chat_scroll_script():
    """اسکرول خودکار نرم به آخرین پیام در پنجره چت"""
    script = """<script>
    (function(){
        const doc = window.parent.document;
        const scroll = () => {
            const m = doc.querySelector('section.main') || doc.querySelector('.main');
            if(m) {
                m.scrollTo({top: m.scrollHeight, behavior: 'smooth'});
            }
        };
        setTimeout(scroll, 100);
        const obs = new MutationObserver(() => { scroll(); });
        obs.observe(doc.body, {childList: true, subtree: true});
    })();
    </script>"""
    components.html(script, height=0, width=0)


def inject_floating_action_buttons():
    """
    تزریق دکمه‌های شناور (کپی کل گفتگو، اسکرول به پایین، اسکرول به بالا)
    """
    js_script = """
    <script>
    (function() {
        const doc = window.parent.document;
        if (doc.getElementById('arad-floating-actions')) return;

        const container = doc.createElement('div');
        container.id = 'arad-floating-actions';
        container.style.cssText = `
            position: fixed;
            bottom: 30px;
            left: 30px;
            z-index: 999999;
            display: flex;
            flex-direction: column;
            gap: 10px;
        `;

        const btnStyle = `
            border: none;
            border-radius: 50%;
            width: 44px;
            height: 44px;
            color: white;
            font-size: 17px;
            cursor: pointer;
            box-shadow: 0 6px 16px rgba(0,0,0,0.3);
            transition: all 0.25s cubic-bezier(0.175, 0.885, 0.32, 1.275);
            display: flex;
            align-items: center;
            justify-content: center;
            backdrop-filter: blur(8px);
        `;

        // 1. دکمه کپی کل چت
        const copyBtn = doc.createElement('button');
        copyBtn.innerHTML = '📋';
        copyBtn.title = "کپی تمام گفتگوی جاری";
        copyBtn.style.cssText = btnStyle + "background: linear-gradient(135deg, #10b981, #059669);";
        copyBtn.onclick = () => {
            const messages = doc.querySelectorAll('[data-testid="stChatMessage"]');
            let fullText = "";
            if (messages.length > 0) {
                messages.forEach(msg => {
                    fullText += msg.innerText + "\\n\\n====================\\n\\n";
                });
            } else {
                const markdowns = doc.querySelectorAll('.stMarkdown');
                markdowns.forEach(m => fullText += m.innerText + "\\n");
            }

            if (fullText.trim()) {
                navigator.clipboard.writeText(fullText).then(() => {
                    const original = copyBtn.innerHTML;
                    copyBtn.innerHTML = '✅';
                    setTimeout(() => { copyBtn.innerHTML = original; }, 2000);
                });
            } else {
                alert("محتوایی برای کپی وجود ندارد.");
            }
        };

        // 2. دکمه اسکرول به پایین
        const scrollBottomBtn = doc.createElement('button');
        scrollBottomBtn.innerHTML = '⬇️';
        scrollBottomBtn.title = "برو به انتهای پیام‌ها";
        scrollBottomBtn.style.cssText = btnStyle + "background: linear-gradient(135deg, #6366f1, #4f46e5);";
        scrollBottomBtn.onclick = () => {
            const main = doc.querySelector('section.main') || doc.querySelector('.main') || window;
            if(main.scrollTo) {
                main.scrollTo({ top: main.scrollHeight || 999999, behavior: 'smooth' });
            }
        };

        // 3. دکمه اسکرول به بالا
        const scrollTopBtn = doc.createElement('button');
        scrollTopBtn.innerHTML = '⬆️';
        scrollTopBtn.title = "برو به ابتدای صفحه";
        scrollTopBtn.style.cssText = btnStyle + "background: rgba(30, 41, 59, 0.85); border: 1px solid rgba(255,255,255,0.1);";
        scrollTopBtn.onclick = () => {
            const main = doc.querySelector('section.main') || doc.querySelector('.main') || window;
            if(main.scrollTo) {
                main.scrollTo({ top: 0, behavior: 'smooth' });
            }
        };

        [copyBtn, scrollBottomBtn, scrollTopBtn].forEach(b => {
            b.onmouseenter = () => { b.style.transform = 'translateY(-3px) scale(1.08)'; };
            b.onmouseleave = () => { b.style.transform = 'translateY(0) scale(1)'; };
        });

        container.appendChild(scrollTopBtn);
        container.appendChild(copyBtn);
        container.appendChild(scrollBottomBtn);
        doc.body.appendChild(container);
    })();
    </script>
    """
    components.html(js_script, height=0, width=0)


def setup_page_config(page_icon: str = "🤖"):
    """تنظیمات صفحه استریم‌لیت و تزریق استایل‌های سراسری"""
    st.set_page_config(
        page_title="AradGPT Pro | سامانه جامع هوش مصنوعی",
        page_icon=page_icon,
        layout="wide",
        initial_sidebar_state="expanded",
    )
    st.markdown(load_advanced_css(), unsafe_allow_html=True)
    inject_copy_button_script()
    inject_floating_action_buttons()
