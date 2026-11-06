# main.py
"""
سرور اصلی سامانه AradGPT Pro 2.0 (FastAPI Core)
ارائه معماری استاندارد REST API، استریم زنده Server-Sent Events (SSE)،
احراز هویت، کاتالوگ پویای مدل‌ها به ازای هر ارائه‌دهنده و رابط کاربری مدرن SPA
"""

import os
import json
import base64
import asyncio
from typing import Optional, List, Dict, Any
from fastapi import FastAPI, Request, Response, Depends, HTTPException, status, UploadFile, File, Form
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# ماژول‌های داخلی سیستم
from modules.database import (
    init_db,
    get_user,
    create_user,
    update_user_password,
    update_user_role,
    delete_user,
    update_balance,
    get_all_users_df,
    get_user_sessions,
    load_session_messages,
    save_session_messages,
    create_new_session,
    rename_session,
    delete_session,
    log_usage,
    get_user_logs_df,
    get_logs_df,
    get_bank_accounts,
    add_bank_account,
    delete_bank_account,
    submit_payment_request,
    get_pending_payments,
    get_all_payment_requests,
    get_user_payment_requests,
    process_payment_request,
    save_image_history,
    get_user_images_history,
    get_system_stats,
    get_setting,
    set_setting
)
from modules.auth import check_login, register_user
from modules.config import (
    get_active_provider_key,
    get_active_base_url,
    get_active_api_key,
    get_usd_to_toman,
    get_welcome_bonus,
    set_config_value,
    APP_VERSION
)
from modules.catalog import (
    get_all_providers,
    get_models_for_provider,
    find_model_in_provider,
    normalize_model_id,
    MODEL_CATEGORIES,
    PROVIDER_CATALOGS
)
from modules.ai_client import (
    get_client,
    test_api_connection,
    clear_client_cache,
    get_current_provider_info
)
from modules.pricing import (
    calculate_text_cost,
    calculate_image_cost,
    calculate_audio_tts_cost,
    calculate_audio_stt_cost,
    get_model_info
)
from modules.utils import (
    count_message_tokens,
    count_string_tokens,
    extract_text_from_file
)
from modules.knowledge import (
    create_collection,
    get_user_collections,
    delete_collection,
    add_document_to_collection,
    get_collection_documents,
    delete_document,
    search_knowledge_collection
)

# ایجاد اپلیکیشن FastAPI
app = FastAPI(
    title="AradGPT Pro API",
    description="پلتفرم یکپارچه هوش مصنوعی چندرسانه‌ای با پشتیبانی منعطف از هرگونه ارائه‌دهنده",
    version=APP_VERSION
)

# تنظیمات CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# مونت کردن فایل‌های استاتیک، فونت‌ها و تصاویر
os.makedirs("static/css", exist_ok=True)
os.makedirs("static/js", exist_ok=True)
os.makedirs("templates", exist_ok=True)
os.makedirs("assets", exist_ok=True)
os.makedirs("fonts", exist_ok=True)

app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/assets", StaticFiles(directory="assets"), name="assets")
app.mount("/fonts", StaticFiles(directory="fonts"), name="fonts")


@app.on_event("startup")
def on_startup():
    """راه‌اندازی اولیه پایگاه‌داده و جدول‌ها"""
    init_db()


# ==========================================
# --- وابستگی احراز هویت (AUTH DEPENDENCY) ---
# ==========================================
def get_current_user(request: Request) -> Optional[Dict[str, Any]]:
    """استخراج کاربر لاگین شده از کوکی نشست یا هدر Authorization"""
    username = request.cookies.get("session_user")
    if not username:
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            username = auth_header.split(" ")[1]

    if not username:
        return None

    user = get_user(username)
    if not user:
        return None

    return {
        "username": user[0],
        "balance": float(user[2]),
        "role": user[3],
        "created_at": user[4] if len(user) > 4 else None
    }


def require_auth(request: Request) -> Dict[str, Any]:
    """اعتبارسنجی اجباری ورود کاربر"""
    user = get_current_user(request)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="لطفاً ابتدا وارد حساب کاربری خود شوید.")
    return user


def require_admin(request: Request) -> Dict[str, Any]:
    """اعتبارسنجی دسترسی مدیر ارشد"""
    user = require_auth(request)
    if user.get("role") != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="شما مجوز دسترسی به این بخش مدیریتی را ندارید.")
    return user


# ==========================================
# --- 1. وب‌پیج اصلی (SPA ROUTE) ---
# ==========================================
@app.get("/", response_class=HTMLResponse)
def serve_index(request: Request):
    """سرو کردن صفحه اصلی وب بدون استفاده از Streamlit"""
    index_file = os.path.join("templates", "index.html")
    if os.path.exists(index_file):
        with open(index_file, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    return HTMLResponse("<h1>در حال بارگذاری AradGPT Pro...</h1>")


# ==========================================
# --- 2. اندپوینت‌های احراز هویت (AUTH APIS) ---
# ==========================================
class LoginRequest(BaseModel):
    username: str
    password: str


class RegisterRequest(BaseModel):
    username: str
    password: str
    confirm_password: str


@app.post("/api/auth/login")
def api_login(req: LoginRequest, response: Response):
    user_data = check_login(req.username, req.password)
    if not user_data:
        raise HTTPException(status_code=400, detail="نام کاربری یا رمز عبور اشتباه است.")

    # ست کردن کوکی نشست
    response.set_cookie(
        key="session_user",
        value=user_data["username"],
        httponly=True,
        max_age=60 * 60 * 24 * 7,  # ۷ روز
        samesite="lax"
    )
    return {"success": True, "user": user_data}


@app.post("/api/auth/register")
def api_register(req: RegisterRequest, response: Response):
    success, user_obj, msg = register_user(req.username, req.password, req.confirm_password)
    if not success:
        raise HTTPException(status_code=400, detail=msg)

    response.set_cookie(
        key="session_user",
        value=user_obj["username"],
        httponly=True,
        max_age=60 * 60 * 24 * 7,
        samesite="lax"
    )
    return {"success": True, "message": msg, "user": user_obj}


@app.get("/api/auth/me")
def api_get_me(request: Request):
    user = get_current_user(request)
    if not user:
        return {"authenticated": False}
    return {"authenticated": True, "user": user}


@app.post("/api/auth/logout")
def api_logout(response: Response):
    response.delete_cookie("session_user")
    return {"success": True}


# ==========================================
# --- 3. ارائه‌دهنده‌ها و کاتالوگ مدل‌ها ---
# ==========================================
@app.get("/api/providers")
def api_get_providers():
    """دریافت کلیه ارائه‌دهنده‌ها به همراه ارائه‌دهنده فعال جاری"""
    active_key = get_active_provider_key()
    providers = get_all_providers()
    for p in providers:
        p["is_active"] = (p["key"] == active_key)
    return {
        "active_provider": active_key,
        "providers": providers,
        "usd_to_toman": get_usd_to_toman()
    }


@app.get("/api/models")
def api_get_models(provider: Optional[str] = None, type: Optional[str] = None):
    """دریافت لیست مدل‌های دقیق برای یک ارائه‌دهنده به همراه دسته‌بندی‌ها"""
    if not provider:
        provider = get_active_provider_key()

    models = get_models_for_provider(provider, type)
    usd_rate = get_usd_to_toman()

    # تبدیل قیمت‌ها به تومان جهت نمایش ساده در فرانت‌اند
    enhanced_models = []
    for m in models:
        copy_m = dict(m)
        in_p = copy_m.get("input_price", 0.0)
        out_p = copy_m.get("output_price", 0.0)
        copy_m["input_price_toman"] = int(in_p * usd_rate)
        copy_m["output_price_toman"] = int(out_p * usd_rate)
        enhanced_models.append(copy_m)

    return {
        "provider": provider,
        "count": len(enhanced_models),
        "categories": MODEL_CATEGORIES,
        "models": enhanced_models
    }


# ==========================================
# --- 4. استودیو چت و استریم پاسخ (CHAT APIS) ---
# ==========================================
class ChatStreamRequest(BaseModel):
    session_id: Optional[str] = None
    model: str
    messages: List[Dict[str, Any]]
    system_prompt: Optional[str] = "You are AradGPT Pro, an intelligent, helpful Persian and English AI assistant."
    temperature: Optional[float] = 0.7
    knowledge_collection_id: Optional[str] = None


# ==========================================
# --- 4.1 پایگاه دانش و جستجوی معنایی (KNOWLEDGE & RAG APIS) ---
# ==========================================
class CreateCollectionRequest(BaseModel):
    title: str
    description: Optional[str] = ""
    icon: Optional[str] = "📚"

class AddDocumentRequest(BaseModel):
    title: str
    content: str

class SearchKnowledgeRequest(BaseModel):
    collection_id: str
    query: str
    top_k: Optional[int] = 4

@app.get("/api/knowledge/collections")
def api_get_knowledge_collections(user: Dict[str, Any] = Depends(require_auth)):
    cols = get_user_collections(user["username"])
    return {"collections": cols}

@app.post("/api/knowledge/collections")
def api_create_knowledge_collection(req: CreateCollectionRequest, user: Dict[str, Any] = Depends(require_auth)):
    col = create_collection(user["username"], req.title, req.description, req.icon)
    return {"success": True, "collection": col}

@app.delete("/api/knowledge/collections/{collection_id}")
def api_delete_knowledge_collection(collection_id: str, user: Dict[str, Any] = Depends(require_auth)):
    ok = delete_collection(collection_id, user["username"])
    return {"success": ok}

@app.get("/api/knowledge/collections/{collection_id}/documents")
def api_get_knowledge_documents(collection_id: str, user: Dict[str, Any] = Depends(require_auth)):
    docs = get_collection_documents(collection_id, user["username"])
    return {"documents": docs}

@app.post("/api/knowledge/collections/{collection_id}/documents")
def api_add_knowledge_document(collection_id: str, req: AddDocumentRequest, user: Dict[str, Any] = Depends(require_auth)):
    doc = add_document_to_collection(collection_id, user["username"], req.title, req.content)
    return {"success": True, "document": doc}

@app.post("/api/knowledge/collections/{collection_id}/upload")
async def api_upload_knowledge_document(collection_id: str, file: UploadFile = File(...), user: Dict[str, Any] = Depends(require_auth)):
    extracted_text, err = extract_text_from_file(file)
    if err:
        raise HTTPException(status_code=400, detail=err)
    doc = add_document_to_collection(collection_id, user["username"], file.filename, extracted_text)
    return {"success": True, "document": doc}

@app.delete("/api/knowledge/documents/{document_id}")
def api_delete_knowledge_document(document_id: str, user: Dict[str, Any] = Depends(require_auth)):
    ok = delete_document(document_id, user["username"])
    return {"success": ok}

@app.post("/api/knowledge/search")
def api_search_knowledge(req: SearchKnowledgeRequest, user: Dict[str, Any] = Depends(require_auth)):
    hits = search_knowledge_collection(req.collection_id, req.query, req.top_k)
    return {"results": hits}


@app.get("/api/chat/sessions")
def api_get_chat_sessions(user: Dict[str, Any] = Depends(require_auth)):
    sessions = get_user_sessions(user["username"])
    return [{"id": s[0], "title": s[1], "updated_at": s[2]} for s in sessions]


@app.get("/api/chat/sessions/{session_id}")
def api_get_chat_session_messages(session_id: str, user: Dict[str, Any] = Depends(require_auth)):
    messages = load_session_messages(session_id)
    return {"session_id": session_id, "messages": messages}


@app.post("/api/chat/sessions")
def api_create_chat_session(title: Optional[str] = "گفتگوی جدید", user: Dict[str, Any] = Depends(require_auth)):
    sess_id = create_new_session(user["username"], title)
    return {"session_id": sess_id, "title": title}


class RenameSessionRequest(BaseModel):
    title: str


@app.put("/api/chat/sessions/{session_id}")
async def api_rename_chat_session(session_id: str, request: Request, user: Dict[str, Any] = Depends(require_auth)):
    new_title = ""
    try:
        data = await request.json()
        new_title = data.get("title", "")
    except Exception:
        try:
            form = await request.form()
            new_title = form.get("title", "")
        except Exception:
            pass

    if new_title:
        rename_session(session_id, str(new_title).strip())
        return {"success": True}
    raise HTTPException(status_code=400, detail="عنوان نامعتبر است.")


@app.delete("/api/chat/sessions/{session_id}")
def api_delete_chat_session(session_id: str, user: Dict[str, Any] = Depends(require_auth)):
    delete_session(session_id)
    return {"success": True}


@app.post("/api/chat/extract-file")
async def api_extract_file(file: UploadFile = File(...), user: Dict[str, Any] = Depends(require_auth)):
    """استخراج متن از فایل ضمیمه شده (PDF, Word, TXT, CSV)"""
    extracted_text, err = extract_text_from_file(file)
    if err:
        raise HTTPException(status_code=400, detail=err)

    tok_count = count_string_tokens(extracted_text)
    return {
        "filename": file.filename,
        "text": extracted_text,
        "token_estimate": tok_count
    }


@app.post("/api/chat/stream")
async def api_chat_stream(req: ChatStreamRequest, user: Dict[str, Any] = Depends(require_auth)):
    """استریم توکن‌به‌توکن پاسخ هوش مصنوعی به صورت Server-Sent Events (SSE)"""
    provider_key = get_active_provider_key()
    resolved_model = normalize_model_id(provider_key, req.model)

    # بررسی وضعیت رایگان بودن مدل
    model_info = get_model_info(resolved_model, provider_key)
    is_model_free = model_info.get("is_free", False) or (model_info.get("input_price", 1.0) == 0.0 and model_info.get("output_price", 3.0) == 0.0)

    # بررسی موجودی کاربر (فقط برای مدل‌های تجاری و غیررایگان)
    fresh_user = get_user(user["username"])
    current_balance = fresh_user[2] if fresh_user else 0.0

    if not is_model_free and current_balance < 20:
        raise HTTPException(status_code=400, detail="موجودی کیف پول شما کافی نیست. لطفاً حساب خود را شارژ فرمایید.")

    client = get_client()
    if not client:
        raise HTTPException(status_code=500, detail="ارتباط با سرویس هوش مصنوعی برقرار نیست. کلید API تنظیم نشده است.")

    session_id = req.session_id
    db_history = load_session_messages(session_id) if session_id else []

    # تلفیق هوشمند تاریخچه پیام‌ها برای اطمینان ۱۰۰٪ از حفظ زمینه مکالمه و عدم فراموشی
    if db_history and len(req.messages) <= 2 and len(db_history) >= len(req.messages):
        # کاربر فقط پیام جدید یا آخرین پیام‌ها را فرستاده است؛ سوابق قبلی از دیتابیس حفظ می‌شوند
        full_conversation = list(db_history)
        for m in req.messages:
            if not any(dm.get("role") == m.get("role") and dm.get("content") == m.get("content") for dm in full_conversation[-3:]):
                full_conversation.append({"role": m["role"], "content": m["content"]})
    else:
        full_conversation = list(req.messages)

    if not session_id:
        first_user_text = next((m["content"] for m in full_conversation if m["role"] == "user"), "گفتگوی جدید")
        session_id = create_new_session(user["username"], first_user_text)

    # آماده‌سازی پیام‌ها برای ارسال به OpenAI / OpenRouter
    api_messages = []

    # اتصال هوشمند به پایگاه دانش و تزریق اسناد مرجع (Semantic RAG)
    if req.knowledge_collection_id:
        last_user_text = next((m["content"] for m in reversed(full_conversation) if m["role"] == "user"), "")
        if last_user_text:
            knowledge_hits = search_knowledge_collection(req.knowledge_collection_id, last_user_text, top_k=3)
            if knowledge_hits:
                relevant_snippets = [f"📄 [سند: {h['title']} - تطابق: {int(h['score']*100)}%]:\n{h['text']}" for h in knowledge_hits if h["score"] > 0.12]
                if relevant_snippets:
                    rag_block = "\n\n".join(relevant_snippets)
                    knowledge_sys = (
                        f"\n\n[اسناد مرجع از پایگاه دانش کاربر]:\n{rag_block}\n\n"
                        "[دستورالعمل: در صورتی که پرسش کاربر مرتبط با این اسناد است، پاسخی موثق و مستند بر مبنای اطلاعات فوق ارائه فرما.]"
                    )
                    api_messages.append({"role": "system", "content": knowledge_sys})

    if req.system_prompt and "o1" not in resolved_model:
        api_messages.append({"role": "system", "content": req.system_prompt})

    # ارسال آخرین ۳۰ پیام برای حفظ کامل کانتکست مکالمه و جلوگیری از سرریز حافظه
    recent_messages = full_conversation[-30:] if len(full_conversation) > 30 else full_conversation
    for m in recent_messages:
        if m.get("content"):
            api_messages.append({"role": m["role"], "content": m["content"]})

    def stream_generator():
        full_reply = ""
        try:
            kwargs = {
                "model": resolved_model,
                "messages": api_messages,
                "stream": True
            }
            if "o1" not in resolved_model and "o3" not in resolved_model:
                kwargs["temperature"] = float(req.temperature)

            stream = client.chat.completions.create(**kwargs)

            for chunk in stream:
                if not chunk.choices or not chunk.choices[0].delta:
                    continue
                delta = chunk.choices[0].delta
                delta_text = getattr(delta, "content", None)
                reasoning_text = getattr(delta, "reasoning", None) or getattr(delta, "reasoning_content", None)

                if reasoning_text:
                    yield f"data: {json.dumps({'reasoning': reasoning_text}, ensure_ascii=False)}\n\n"

                if delta_text:
                    full_reply += delta_text
                    data_obj = {"delta": delta_text}
                    yield f"data: {json.dumps(data_obj, ensure_ascii=False)}\n\n"

            # محاسبه توکن و کسر موجودی پس از اتمام استریم
            in_tokens = count_message_tokens(api_messages, resolved_model)
            out_tokens = count_string_tokens(full_reply, resolved_model)
            if is_model_free:
                cost = 0.0
            else:
                cost = calculate_text_cost(resolved_model, in_tokens, out_tokens, provider_key)
                update_balance(user["username"], -cost)
            log_usage(user["username"], resolved_model, "chat", cost)

            # ذخیره سشن کامل با پیام جدید در دیتابیس
            all_messages = list(full_conversation)
            all_messages.append({"role": "assistant", "content": full_reply})
            save_session_messages(session_id, all_messages)

            # دریافت موجودی جدید
            updated_u = get_user(user["username"])
            new_bal = updated_u[2] if updated_u else 0.0

            done_obj = {
                "done": True,
                "session_id": session_id,
                "input_tokens": in_tokens,
                "output_tokens": out_tokens,
                "cost": cost,
                "new_balance": new_bal
            }
            yield f"data: {json.dumps(done_obj, ensure_ascii=False)}\n\n"

        except Exception as e:
            err_obj = {"error": str(e)}
            yield f"data: {json.dumps(err_obj, ensure_ascii=False)}\n\n"

    return StreamingResponse(stream_generator(), media_type="text/event-stream")


# ==========================================
# --- 5. استودیو تصویر (IMAGE APIS) ---
# ==========================================
class ImageGenerateRequest(BaseModel):
    model: str
    prompt: str
    size: Optional[str] = "1024x1024"
    quality: Optional[str] = "standard"


@app.post("/api/image/generate")
def api_generate_image(req: ImageGenerateRequest, user: Dict[str, Any] = Depends(require_auth)):
    fresh_user = get_user(user["username"])
    current_balance = fresh_user[2] if fresh_user else 0.0

    cost = calculate_image_cost(req.model)
    if current_balance < cost:
        raise HTTPException(status_code=400, detail=f"موجودی کیف پول شما کافی نیست. هزینه این تصویر: {int(cost):,} تومان")

    client = get_client()
    if not client:
        raise HTTPException(status_code=500, detail="کلاینت هوش مصنوعی متصل نیست.")

    try:
        kwargs = {
            "model": req.model,
            "prompt": req.prompt.strip(),
            "size": req.size,
            "n": 1
        }
        if "dall-e-3" in req.model:
            kwargs["quality"] = req.quality

        res = client.images.generate(**kwargs)

        if not res or not res.data:
            raise HTTPException(status_code=500, detail="پاسخی از سرور تولید تصویر دریافت نشد.")

        image_url = res.data[0].url

        update_balance(user["username"], -cost)
        log_usage(user["username"], req.model, "image", cost)
        save_image_history(user["username"], req.prompt, image_url, req.model, cost)

        updated_u = get_user(user["username"])
        new_bal = updated_u[2] if updated_u else 0.0

        return {
            "success": True,
            "image_url": image_url,
            "cost": cost,
            "new_balance": new_bal
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"خطا در ایجاد تصویر: {str(e)}")


@app.get("/api/image/history")
def api_get_image_history(user: Dict[str, Any] = Depends(require_auth)):
    rows = get_user_images_history(user["username"], limit=30)
    result = []
    for r in rows:
        result.append({
            "id": r[0],
            "prompt": r[1],
            "image_url": r[2],
            "model": r[3],
            "cost": r[4],
            "created_at": r[5]
        })
    return result


# ==========================================
# --- 6. استودیو صدا (AUDIO APIS) ---
# ==========================================
class TTSRequest(BaseModel):
    model: str
    input_text: str
    voice: Optional[str] = "alloy"
    speed: Optional[float] = 1.0


@app.post("/api/audio/tts")
def api_generate_tts(req: TTSRequest, user: Dict[str, Any] = Depends(require_auth)):
    fresh_user = get_user(user["username"])
    current_balance = fresh_user[2] if fresh_user else 0.0

    cost = calculate_audio_tts_cost(req.model, len(req.input_text))
    if current_balance < cost:
        raise HTTPException(status_code=400, detail=f"موجودی ناکافی. هزینه صوت: {int(cost):,} تومان")

    client = get_client()
    if not client:
        raise HTTPException(status_code=500, detail="کلاینت هوش مصنوعی متصل نیست.")

    try:
        response = client.audio.speech.create(
            model=req.model,
            voice=req.voice,
            input=req.input_text.strip(),
            speed=req.speed
        )

        audio_base64 = base64.b64encode(response.content).decode("utf-8")
        update_balance(user["username"], -cost)
        log_usage(user["username"], req.model, "audio_tts", cost)

        updated_u = get_user(user["username"])
        return {
            "success": True,
            "audio_base64": audio_base64,
            "mime_type": "audio/mp3",
            "cost": cost,
            "new_balance": updated_u[2]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"خطا در تولید صوت: {str(e)}")


@app.post("/api/audio/stt")
async def api_generate_stt(
    model: str = Form(...),
    language: Optional[str] = Form("fa"),
    file: UploadFile = File(...),
    user: Dict[str, Any] = Depends(require_auth)
):
    fresh_user = get_user(user["username"])
    current_balance = fresh_user[2] if fresh_user else 0.0

    if current_balance < 100:
        raise HTTPException(status_code=400, detail="حداقل موجودی ۱۰۰ تومان برای پیاده‌سازی صوت نیاز است.")

    client = get_client()
    if not client:
        raise HTTPException(status_code=500, detail="کلاینت هوش مصنوعی متصل نیست.")

    try:
        file_bytes = await file.read()
        file_tuple = (file.filename or "recording.wav", file_bytes, file.content_type or "audio/wav")

        pure_mod = model.replace("gapgpt/", "")
        kwargs = {
            "model": pure_mod,
            "file": file_tuple
        }
        if language in ["fa", "en"]:
            kwargs["language"] = language

        transcript_obj = client.audio.transcriptions.create(**kwargs)
        extracted_text = transcript_obj.text

        cost = calculate_audio_stt_cost(model, len(extracted_text))
        update_balance(user["username"], -cost)
        log_usage(user["username"], model, "audio_stt", cost)

        updated_u = get_user(user["username"])
        return {
            "success": True,
            "text": extracted_text,
            "cost": cost,
            "new_balance": updated_u[2]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"خطا در پیاده‌سازی صوت: {str(e)}")


# ==========================================
# --- 7. کیف پول و امور مالی (WALLET APIS) ---
# ==========================================
@app.get("/api/wallet/info")
def api_get_wallet_info(user: Dict[str, Any] = Depends(require_auth)):
    fresh_user = get_user(user["username"])
    banks = get_bank_accounts()
    user_requests = get_user_payment_requests(user["username"])
    user_logs = get_user_logs_df(user["username"], limit=50)

    return {
        "balance": fresh_user[2] if fresh_user else 0.0,
        "bank_accounts": banks.to_dict(orient="records"),
        "deposit_requests": user_requests.to_dict(orient="records"),
        "transactions": user_logs.to_dict(orient="records")
    }


@app.post("/api/wallet/deposit")
async def api_submit_deposit(
    amount: int = Form(...),
    receipt: UploadFile = File(...),
    user: Dict[str, Any] = Depends(require_auth)
):
    if amount < 10000:
        raise HTTPException(status_code=400, detail="حداقل مبلغ واریزی ۱۰,۰۰۰ تومان می‌باشد.")

    receipt_bytes = await receipt.read()
    submit_payment_request(user["username"], amount, receipt_bytes)
    return {"success": True, "message": "فیش با موفقیت ثبت شد و در انتظار تایید مدیریت می‌باشد."}


# ==========================================
# --- 8. کنترل‌پنل مدیریت ارشد (ADMIN APIS) ---
# ==========================================
@app.get("/api/admin/stats")
def api_admin_stats(admin: Dict[str, Any] = Depends(require_admin)):
    return get_system_stats()


@app.get("/api/admin/users")
def api_admin_get_users(query: Optional[str] = None, admin: Dict[str, Any] = Depends(require_admin)):
    df = get_all_users_df()
    if query:
        df = df[df["username"].str.contains(query.strip().lower(), na=False)]
    return df.to_dict(orient="records")


@app.post("/api/admin/users")
def api_admin_create_user(
    username: str = Form(...),
    password: str = Form(...),
    balance: float = Form(20000),
    role: str = Form("user"),
    admin: Dict[str, Any] = Depends(require_admin)
):
    if not username or not password:
        raise HTTPException(status_code=400, detail="نام کاربری و رمز عبور الزامی است.")
    if create_user(username, password, balance, role):
        return {"success": True}
    raise HTTPException(status_code=400, detail="این نام کاربری قبلاً ثبت شده است.")


@app.put("/api/admin/users/{target_user}/balance")
def api_admin_update_balance(target_user: str, amount: float = Form(...), admin: Dict[str, Any] = Depends(require_admin)):
    update_balance(target_user, amount)
    return {"success": True}


@app.put("/api/admin/users/{target_user}/password")
def api_admin_update_password(target_user: str, new_password: str = Form(...), admin: Dict[str, Any] = Depends(require_admin)):
    if update_user_password(target_user, new_password):
        return {"success": True}
    raise HTTPException(status_code=400, detail="خطا در تغییر رمز عبور.")


@app.put("/api/admin/users/{target_user}/role")
def api_admin_update_role(target_user: str, role: str = Form(...), admin: Dict[str, Any] = Depends(require_admin)):
    if update_user_role(target_user, role):
        return {"success": True}
    raise HTTPException(status_code=400, detail="خطا در تغییر نقش کاربر.")


@app.delete("/api/admin/users/{target_user}")
def api_admin_delete_user(target_user: str, admin: Dict[str, Any] = Depends(require_admin)):
    if target_user == "admin":
        raise HTTPException(status_code=400, detail="ادمین اصلی سیستم قابل حذف نیست.")
    if delete_user(target_user):
        return {"success": True}
    raise HTTPException(status_code=400, detail="خطا در حذف کاربر.")


@app.get("/api/admin/deposits")
def api_admin_get_deposits(admin: Dict[str, Any] = Depends(require_admin)):
    pending = get_pending_payments()
    pending_list = []
    for r in pending:
        rid, u, amt, img_bytes, created_at, note = r
        img_b64 = base64.b64encode(img_bytes).decode("utf-8") if img_bytes else ""
        pending_list.append({
            "id": rid,
            "username": u,
            "amount": amt,
            "created_at": created_at,
            "receipt_b64": img_b64,
            "admin_note": note
        })

    all_history = get_all_payment_requests(60)
    return {
        "pending": pending_list,
        "history": all_history.to_dict(orient="records")
    }


@app.post("/api/admin/deposits/{req_id}/process")
def api_admin_process_deposit(
    req_id: int,
    action: str = Form(...),  # APPROVED or REJECTED
    admin_note: str = Form(""),
    admin: Dict[str, Any] = Depends(require_admin)
):
    if process_payment_request(req_id, action, admin_note):
        return {"success": True}
    raise HTTPException(status_code=400, detail="خطا در پردازش درخواست فیش.")


@app.get("/api/admin/bank-accounts")
def api_admin_get_banks(admin: Dict[str, Any] = Depends(require_admin)):
    df = get_bank_accounts()
    return df.to_dict(orient="records")


@app.post("/api/admin/bank-accounts")
def api_admin_add_bank(
    bank_name: str = Form(...),
    owner_name: str = Form(...),
    card_number: str = Form(...),
    sheba_number: str = Form(""),
    admin: Dict[str, Any] = Depends(require_admin)
):
    add_bank_account(bank_name, owner_name, card_number, sheba_number)
    return {"success": True}


@app.delete("/api/admin/bank-accounts/{account_id}")
def api_admin_delete_bank(account_id: int, admin: Dict[str, Any] = Depends(require_admin)):
    delete_bank_account(account_id)
    return {"success": True}


@app.get("/api/admin/settings")
def api_admin_get_settings(admin: Dict[str, Any] = Depends(require_admin)):
    return {
        "active_provider": get_active_provider_key(),
        "base_url": get_active_base_url(),
        "api_key": get_active_api_key(),
        "usd_to_toman": get_usd_to_toman(),
        "welcome_bonus": get_welcome_bonus()
    }


class SettingsUpdateRequest(BaseModel):
    active_provider: str
    base_url: str
    api_key: str
    usd_to_toman: int
    welcome_bonus: int


@app.post("/api/admin/settings")
def api_admin_update_settings(req: SettingsUpdateRequest, admin: Dict[str, Any] = Depends(require_admin)):
    set_setting("ACTIVE_PROVIDER", req.active_provider.strip().lower())
    set_setting("AI_BASE_URL", req.base_url.strip())
    set_setting("AI_API_KEY", req.api_key.strip())
    set_setting("USD_TO_TOMAN", str(req.usd_to_toman))
    set_setting("WELCOME_BONUS", str(req.welcome_bonus))

    clear_client_cache()
    return {"success": True, "message": "تنظیمات با موفقیت ذخیره و اعمال گردید."}


class TestApiRequest(BaseModel):
    api_key: str
    base_url: str


@app.post("/api/admin/test-api")
def api_admin_test_api(req: TestApiRequest, admin: Dict[str, Any] = Depends(require_admin)):
    success, msg, latency, models = test_api_connection(req.api_key, req.base_url)
    return {
        "success": success,
        "message": msg,
        "latency_ms": latency,
        "models": models
    }


@app.get("/api/admin/logs")
def api_admin_get_logs(admin: Dict[str, Any] = Depends(require_admin)):
    df = get_logs_df(limit=300)
    return df.to_dict(orient="records")


# نقطه اجرای سرور مستقیم
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8501, reload=True)
