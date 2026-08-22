# modules/ui.py
import base64
import os
import json
import streamlit as st
import streamlit.components.v1 as components

CHAT_INPUT_PLACEHOLDER = "از من بپرس..."

def _load_font(font_name, file_name):
    """لود کردن فونت لوکال"""
    font_path = os.path.join("fonts", file_name)
    if os.path.exists(font_path):
        try:
            with open(font_path, "rb") as f:
                data = f.read()
                return base64.b64encode(data).decode()
        except Exception:
            pass
    return None

def load_advanced_css():
    vazir_b64 = _load_font("Vazirmatn", "Vazir.ttf")
    
    # اولویت با فونت لوکال است، اگر نبود از گوگل می‌خواند
    font_face = ""
    if vazir_b64:
        font_face = f"""
        @font-face {{ 
            font-family: 'Vazirmatn'; 
            src: url('data:font/ttf;base64,{vazir_b64}') format('truetype'); 
            font-weight: normal; 
        }}
        """
    
    # CSS کامل Qwen-Style
    return f"""
    <style>
    /* === Font Setup === */
    @import url('https://fonts.googleapis.com/css2?family=Vazirmatn:wght@300;400;500;600;700&display=swap');
    {font_face}

    /* === Global Settings === */
    :root {{
        --primary-gradient: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        --sidebar-bg: linear-gradient(160deg, #1e293b 0%, #0f172a 100%);
        --card-bg: rgba(255, 255, 255, 0.95);
        --dark-card-bg: #1e293b;
        --border-color: rgba(255, 255, 255, 0.1);
        --text-primary: #1e293b;
        --text-secondary: #64748b;
        --text-light: #94a3b8;
    }}

    /* === Persian Typography System === */
    html, body, [class*="css"], p, div, span, li, td, th {{
        font-family: 'Vazirmatn', 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif !important;
    }}
    
    /* تنظیم جهت پیش‌فرض RTL */
    .stMarkdown p, .stMarkdown li, .stSelectbox, .stTextInput label, .stTextArea label {{
        text-align: right !important;
        direction: rtl !important;
    }}

    /* === English/LTR Content Handling === */
    .stMarkdown code, 
    .stCodeBlock, 
    pre, 
    code, 
    .math-element,
    .ltr-content,
    .stJson,
    .stTable {{
        direction: ltr !important;
        text-align: left !important;
        font-family: 'Consolas', 'Monaco', 'Courier New', monospace !important;
    }}

    /* === Sidebar - Qwen Style === */
    [data-testid="stSidebar"] {{
        background: var(--sidebar-bg);
        border-right: 1px solid var(--border-color);
        backdrop-filter: blur(20px);
        box-shadow: 2px 0 20px rgba(0, 0, 0, 0.1);
    }}
    
    [data-testid="stSidebar"] p, [data-testid="stSidebar"] span, [data-testid="stSidebar"] label {{
        color: var(--text-light) !important;
    }}

    /* Profile Card */
    .user-profile-box {{
        background: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 16px;
        padding: 20px;
        margin: 20px 0;
        text-align: center;
        position: relative;
        overflow: hidden;
        backdrop-filter: blur(10px);
    }}
    .user-profile-box::before {{
        content: "";
        position: absolute;
        top: 0; left: 0; right: 0;
        height: 3px;
        background: var(--primary-gradient);
    }}
    .user-profile-box h3 {{
        color: white !important;
        margin: 0 0 8px 0;
        font-size: 1.1rem;
        font-weight: 600;
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 8px;
    }}
    .user-profile-box p {{
        background: var(--primary-gradient);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        margin: 0;
        font-weight: 700;
        font-size: 1.2rem;
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 8px;
    }}

    /* Navigation Menu */
    .stRadio > div[role="radiogroup"] {{
        display: flex;
        flex-direction: column;
        gap: 6px;
        padding: 0 4px;
    }}
    
    /* مخفی کردن دایره‌های رادیو */
    .stRadio div[role="radiogroup"] label > div:first-child {{
        display: none !important;
    }}

    .stRadio > div[role="radiogroup"] label {{
        background: transparent;
        border: none;
        color: var(--text-light) !important;
        padding: 12px 16px;
        margin: 0;
        border-radius: 12px;
        transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
        display: flex;
        flex-direction: row-reverse;
        align-items: center;
        justify-content: flex-start;
        gap: 12px;
        cursor: pointer;
        position: relative;
        font-weight: 500;
        width: 100%;
    }}

    /* Active State */
    .stRadio > div[role="radiogroup"] label[data-checked="true"] {{
        background: rgba(102, 126, 234, 0.15);
        color: #a5b4fc !important;
        border-right: 3px solid #667eea;
    }}
    .stRadio > div[role="radiogroup"] label[data-checked="true"] p {{
        color: white !important;
        font-weight: bold !important;
    }}

    /* Hover Effects */
    .stRadio > div[role="radiogroup"] label:hover {{
        background: rgba(255, 255, 255, 0.08);
        color: white !important;
        transform: translateX(-3px);
    }}

    /* Chat History Section */
    .chat-history-section {{
        margin-top: 25px;
        padding-top: 15px;
        border-top: 1px solid var(--border-color);
    }}
    .chat-history-section h6 {{
        color: var(--text-light) !important;
        font-size: 0.85rem;
        margin: 0 0 12px 0;
        font-weight: 500;
        text-align: right;
        padding-right: 10px;
    }}

    /* Buttons Styling */
    /* دکمه‌های معمولی (New Chat) */
    [data-testid="stSidebar"] .stButton button {{
        background: linear-gradient(135deg, #10b981 0%, #059669 100%) !important;
        color: white !important;
        border: none !important;
        border-radius: 12px !important;
        padding: 8px 16px !important;
        font-weight: 600 !important;
        box-shadow: 0 4px 10px rgba(16, 185, 129, 0.2) !important;
        transition: all 0.2s ease !important;
        margin-bottom: 8px;
    }}
    
    /* دکمه‌های تاریخچه (شفاف) */
    [data-testid="stSidebar"] .chat-history-item button {{
        background: rgba(255, 255, 255, 0.03) !important;
        box-shadow: none !important;
        color: var(--text-light) !important;
        justify-content: flex-start !important;
        text-align: right !important;
    }}
    [data-testid="stSidebar"] .chat-history-item button:hover {{
        background: rgba(102, 126, 234, 0.1) !important;
        color: white !important;
    }}
    
    /* دکمه خروج (قرمز) - با استفاده از nth-child یا کلاس والد */
    /* چون نمی‌توانیم مستقیم کلاس بدهیم، دکمه آخر سایدبار را هدف می‌گیریم */
    [data-testid="stSidebar"] > div > div:last-child .stButton button {{
        background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%) !important;
        box-shadow: 0 4px 15px rgba(239, 68, 68, 0.3) !important;
        margin-top: 20px;
    }}

    /* === Main Content Cards === */
    .modern-card {{
        background: var(--card-bg);
        border-radius: 20px;
        padding: 30px;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.08);
        border: 1px solid rgba(255, 255, 255, 0.8);
        margin-bottom: 25px;
        position: relative;
        overflow: hidden;
        backdrop-filter: blur(10px);
        text-align: right;
        direction: rtl;
    }}
    .modern-card::before {{
        content: "";
        position: absolute;
        top: 0; right: 0;
        width: 4px;
        height: 100%;
        background: var(--primary-gradient);
    }}

    /* === Input Fields === */
    .stTextInput input, .stTextArea textarea, .stSelectbox {{
        direction: rtl;
        text-align: right;
        background: white !important;
        border-radius: 12px !important;
        border: 1px solid #e2e8f0 !important;
    }}
    
    /* === Tables & Code === */
    .stTable, .stDataFrame {{
        direction: ltr !important;
    }}
    .stCodeBlock {{
        direction: ltr !important;
        text-align: left !important;
        border-radius: 12px !important;
        border: 1px solid #333 !important;
    }}

    /* مخفی‌سازی هدر */
    header, footer, .stAppDeployButton {{ display: none !important; }}
    </style>
    """

def inject_copy_button_script():
    script = """<script>
    (function(){
        const doc=window.parent.document;
        const obs=new MutationObserver(()=>{
            doc.querySelectorAll('[data-testid="stCopyToClipboard"]').forEach(b=>{
                if(!b.classList.contains('p')){b.classList.add('p');}
            });
        });
        obs.observe(doc.body,{childList:true,subtree:true});
    })();
    </script>"""
    components.html(script, height=0, width=0)

def inject_chat_scroll_script():
    script = f"""<script>
    (function(){{
        const doc = window.parent.document;
        const ph = {json.dumps(CHAT_INPUT_PLACEHOLDER)};
        const scroll = () => {{
            const m = doc.querySelector('section.main');
            if(m) m.scrollTo({{top:m.scrollHeight, behavior:'smooth'}});
        }};
        scroll();
        const obs = new MutationObserver(() => {{
            scroll();
        }});
        obs.observe(doc.body, {{childList:true, subtree:true}});
    }})();
    </script>"""
    components.html(script, height=0, width=0)

def setup_page_config(page_icon):
    st.set_page_config(
        page_title="AradGPT Pro",
        page_icon=page_icon,
        layout="wide",
        initial_sidebar_state="expanded",
    )
    st.markdown(load_advanced_css(), unsafe_allow_html=True)
    inject_copy_button_script()
    inject_floating_action_buttons()

def inject_floating_action_buttons():
    """
    تزریق دکمه‌های شناور (کپی و اسکرول) به بدنه اصلی صفحه
    """
    js_script = """
    <script>
    (function() {
        const doc = window.parent.document;
        
        // جلوگیری از ایجاد تکراری دکمه‌ها در صورت رفرش شدن
        if (doc.getElementById('arad-floating-actions')) return;

        // 1. ایجاد کانتینر دکمه‌ها
        const container = doc.createElement('div');
        container.id = 'arad-floating-actions';
        container.style.cssText = `
            position: fixed;
            bottom: 25px;
            left: 25px;
            z-index: 999999;
            display: flex;
            flex-direction: column;
            gap: 12px;
        `;

        // استایل مشترک دکمه‌ها
        const btnStyle = `
            border: none;
            border-radius: 50%;
            width: 45px;
            height: 45px;
            color: white;
            font-size: 18px;
            cursor: pointer;
            box-shadow: 0 4px 12px rgba(0,0,0,0.2);
            transition: all 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275);
            display: flex;
            align-items: center;
            justify-content: center;
            backdrop-filter: blur(5px);
        `;

        // 2. دکمه کپی کل متن (سبز)
        const copyBtn = doc.createElement('button');
        copyBtn.innerHTML = '📋';
        copyBtn.title = "کپی کل گفتگو";
        copyBtn.style.cssText = btnStyle + "background: linear-gradient(135deg, #10b981, #059669);";
        
        copyBtn.onclick = () => {
            // پیدا کردن تمام پیام‌های چت
            const messages = doc.querySelectorAll('[data-testid="stChatMessage"]');
            let fullText = "";
            
            if (messages.length > 0) {
                messages.forEach(msg => {
                    // استخراج متن تمیز
                    fullText += msg.innerText + "\\n\\n-------------------\\n\\n";
                });
            } else {
                // فال‌بک: اگر چت مسیج پیدا نشد، کل متن مارک‌داون را بردار
                const markdowns = doc.querySelectorAll('.stMarkdown');
                markdowns.forEach(m => fullText += m.innerText + "\\n");
            }

            if (fullText.trim()) {
                navigator.clipboard.writeText(fullText).then(() => {
                    const originalIcon = copyBtn.innerHTML;
                    copyBtn.innerHTML = '✅';
                    copyBtn.style.transform = 'scale(1.1)';
                    setTimeout(() => {
                        copyBtn.innerHTML = originalIcon;
                        copyBtn.style.transform = 'scale(1)';
                    }, 2000);
                }).catch(err => console.error('Copy failed', err));
            } else {
                alert("متنی برای کپی وجود ندارد!");
            }
        };

        // 3. دکمه اسکرول به پایین (آبی)
        const scrollBtn = doc.createElement('button');
        scrollBtn.innerHTML = '⬇️';
        scrollBtn.title = "برو به پایین";
        scrollBtn.style.cssText = btnStyle + "background: linear-gradient(135deg, #3b82f6, #2563eb);";
        
        scrollBtn.onclick = () => {
            // اسکرول کردن بخش اصلی محتوا
            const main = doc.querySelector('.main');
            if(main) {
                main.scrollTo({ top: main.scrollHeight, behavior: 'smooth' });
            } else {
                window.scrollTo({ top: doc.body.scrollHeight, behavior: 'smooth' });
            }
        };

        // افکت‌های هاور (Hover Effects)
        [copyBtn, scrollBtn].forEach(btn => {
            btn.onmouseenter = () => { 
                btn.style.transform = 'translateY(-3px) scale(1.1)'; 
                btn.style.boxShadow = '0 6px 15px rgba(0,0,0,0.3)';
            };
            btn.onmouseleave = () => { 
                btn.style.transform = 'translateY(0) scale(1)'; 
                btn.style.boxShadow = '0 4px 12px rgba(0,0,0,0.2)';
            };
        });

        // اضافه کردن به صفحه
        container.appendChild(copyBtn);
        container.appendChild(scrollBtn);
        doc.body.appendChild(container);
    })();
    </script>
    """
    components.html(js_script, height=0, width=0)