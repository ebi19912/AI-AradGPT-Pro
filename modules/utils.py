# modules/utils.py
"""
ابزارهای کاربردی سیستم AradGPT Pro
شمارش دقیق توکن‌ها، خواندن فایل‌های متنی و اسناد (PDF, Word, TXT, CSV)، و فرمت‌بندی‌ها
"""

from typing import Tuple, Optional, List, Dict, Any
from .pricing import (
    calculate_text_cost,
    calculate_image_cost,
    calculate_audio_tts_cost,
    calculate_audio_stt_cost,
    get_model_info
)

# تلاش برای ایمپورت tiktoken با فال‌بک ایمن
try:
    import tiktoken
    TIKTOKEN_AVAILABLE = True
except ImportError:
    tiktoken = None
    TIKTOKEN_AVAILABLE = False

# تلاش برای ایمپورت کتابخانه‌های پردازش اسناد
try:
    import pypdf as pdf_lib
except ImportError:
    try:
        import PyPDF2 as pdf_lib
    except ImportError:
        pdf_lib = None

try:
    from docx import Document
except ImportError:
    Document = None


def get_encoding(model: str = "gpt-4o"):
    """دریافت انکودر مناسب بر اساس مدل"""
    if not TIKTOKEN_AVAILABLE or tiktoken is None:
        return None
    try:
        pure_model = model.split("/")[-1] if "/" in model else model
        return tiktoken.encoding_for_model(pure_model)
    except Exception:
        try:
            return tiktoken.get_encoding("cl100k_base")
        except Exception:
            return None


def count_string_tokens(text: str, model: str = "gpt-4o") -> int:
    """
    شمارش دقیق توکن‌های یک متن ساده
    با فال‌بک هوشمند در صورت در دسترس نبودن tiktoken
    """
    if not text:
        return 0

    encoding = get_encoding(model)
    if encoding is not None:
        try:
            return len(encoding.encode(text))
        except Exception:
            pass

    # فال‌بک تخمینی: میانگین ۳.۵ کاراکتر برای هر توکن فارسی/انگلیسی
    return max(1, int(len(text) / 3.5))


def count_message_tokens(messages: List[Dict[str, Any]], model: str = "gpt-4o") -> int:
    """
    شمارش دقیق توکن‌های تاریخچه چت بر اساس استاندارد OpenAI
    """
    if not messages:
        return 0

    encoding = get_encoding(model)
    tokens_per_message = 3
    tokens_per_name = 1

    num_tokens = 0
    for message in messages:
        num_tokens += tokens_per_message
        for key, value in message.items():
            if value:
                if encoding is not None:
                    try:
                        num_tokens += len(encoding.encode(str(value)))
                    except Exception:
                        num_tokens += max(1, int(len(str(value)) / 3.5))
                else:
                    num_tokens += max(1, int(len(str(value)) / 3.5))

                if key == "name":
                    num_tokens += tokens_per_name

    num_tokens += 3  # هر پاسخ با <|start|>assistant<|message|> خاتمه می‌یابد
    return num_tokens


def extract_text_from_file(uploaded_file) -> Tuple[Optional[str], Optional[str]]:
    """
    استخراج متن از انواع فایل‌های آپلود شده (PDF, DOCX, TXT, CSV, JSON, MD, PY)
    خروجی: (متن استخراج شده, پیام خطا در صورت وجود)
    """
    if uploaded_file is None:
        return None, "هیچ فایلی انتخاب نشده است."

    text = ""
    file_type = getattr(uploaded_file, "type", "")
    file_name = getattr(uploaded_file, "name", "").lower()

    try:
        # 1. فایل‌های PDF
        if "pdf" in file_type or file_name.endswith(".pdf"):
            if pdf_lib is None:
                return None, "کتابخانه خواندن PDF (pypdf) روی سرور نصب نیست."

            reader = pdf_lib.PdfReader(uploaded_file)
            total_pages = len(reader.pages)
            if total_pages == 0:
                return None, "فایل PDF خالی است."

            # خواندن حداکثر ۵۰ صفحه برای جلوگیری از سنگین شدن سشن
            for i in range(min(total_pages, 50)):
                page = reader.pages[i]
                extracted = page.extract_text()
                if extracted:
                    text += extracted + "\n"

            if not text.strip():
                return None, "متنی در این فایل PDF یافت نشد (احتمالاً سند اسکن‌شده به صورت عکس است)."

        # 2. فایل‌های Word (.docx)
        elif "wordprocessingml" in file_type or file_name.endswith(".docx"):
            if Document is None:
                return None, "کتابخانه خواندن Word (python-docx) روی سرور نصب نیست."

            doc = Document(uploaded_file)
            for para in doc.paragraphs:
                if para.text:
                    text += para.text + "\n"

        # 3. فایل‌های متنی ساده، کد و CSV
        elif any(file_name.endswith(ext) for ext in [".txt", ".csv", ".json", ".md", ".py", ".html"]):
            raw_bytes = uploaded_file.getvalue()
            # تلاش برای تشخیص انکودینگ
            for encoding in ["utf-8", "utf-8-sig", "cp1256", "latin-1"]:
                try:
                    text = raw_bytes.decode(encoding)
                    break
                except UnicodeDecodeError:
                    continue

        else:
            return None, f"فرمت فایل {file_name} پشتیبانی نمی‌شود. لطفاً فایل PDF, DOCX, TXT یا CSV آپلود فرمایید."

    except Exception as e:
        return None, f"خطا در خواندن فایل: {str(e)}"

    return text.strip(), None
