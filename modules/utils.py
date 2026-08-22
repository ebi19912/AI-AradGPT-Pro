# modules/utils.py
import tiktoken
from .pricing import PRICING_DB, USD_TO_TOMAN
import PyPDF2
from docx import Document


def get_encoding(model="gpt-4o"):
    try:
        return tiktoken.encoding_for_model(model)
    except KeyError:
        return tiktoken.get_encoding("cl100k_base")

def count_string_tokens(text, model="gpt-4o"):
    """
    شمارش دقیق توکن‌های یک متن ساده.
    (نام این تابع اصلاح شد تا با app.py هماهنگ باشد)
    """
    if not text:
        return 0
    encoding = get_encoding(model)
    return len(encoding.encode(text))

def count_message_tokens(messages, model="gpt-4o"):
    """
    شمارش دقیق توکن‌های کل تاریخچه چت (فرمت JSON).
    این تابع مشابه روش رسمی OpenAI عمل می‌کند.
    """
    encoding = get_encoding(model)
    tokens_per_message = 3
    tokens_per_name = 1
    
    num_tokens = 0
    for message in messages:
        num_tokens += tokens_per_message
        for key, value in message.items():
            if value:
                num_tokens += len(encoding.encode(str(value)))
                if key == "name":
                    num_tokens += tokens_per_name
    num_tokens += 3  # هر پاسخ با <|start|>assistant<|message|> شروع می‌شود
    return num_tokens

def calculate_text_cost(model_name, input_tokens, output_tokens):
    """محاسبه قیمت نهایی متن به تومان"""
    if model_name not in PRICING_DB:
        return 0
    
    info = PRICING_DB[model_name]
    # قیمت‌ها در دیتابیس برای 1 میلیون توکن هستند
    # info['input'] قیمت دلاری ورودی است
    
    cost_input = (input_tokens / 1_000_000) * info['input'] * USD_TO_TOMAN
    cost_output = (output_tokens / 1_000_000) * info['output'] * USD_TO_TOMAN
    
    return cost_input + cost_output

def calculate_image_cost(model_name):
    """محاسبه قیمت تصویر به تومان"""
    if model_name in PRICING_DB:
        return PRICING_DB[model_name]['price'] * USD_TO_TOMAN
    return 0



def extract_text_from_file(uploaded_file):
    text = ""
    try:
        if uploaded_file.type == "application/pdf":
            pdf_reader = PyPDF2.PdfReader(uploaded_file)
            for page in pdf_reader.pages:
                extracted = page.extract_text()
                if extracted:
                    text += extracted + "\n"
        elif (uploaded_file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document"):
            doc = Document(uploaded_file)
            for para in doc.paragraphs:
                text += para.text + "\n"
        elif uploaded_file.type in {"text/plain", "text/csv"}:
            text = uploaded_file.getvalue().decode("utf-8")
        else:
            return None, "فرمت پشتیبانی نمی‌شود."
    except Exception as e:
        return None, f"خطا: {e}"
    return text, None