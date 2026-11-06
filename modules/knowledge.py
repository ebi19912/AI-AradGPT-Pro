# modules/knowledge.py
"""
ماژول پیشرفته مدیریت پایگاه دانش (Knowledge Base) و جستجوی معنایی (RAG)
پشتیبانی از ایجاد مجموعه‌های دانش، بارگذاری فایل‌ها/متون، بخش‌بندی (Chunking)،
تولید امبدینگ‌ها (Embeddings) و بازیابی هوشمند محتوا با شباهت برداری (Cosine Similarity)
"""

import os
import re
import json
import uuid
import math
import hashlib
from typing import List, Dict, Any, Optional, Tuple
from modules.database import get_connection
from modules.ai_client import get_client
from modules.config import get_active_provider_key

# ==========================================
# 1. مقداردهی اولیه‌ی جداول پایگاه دانش
# ==========================================
def init_knowledge_db():
    """ایجاد جداول مربوط به پایگاه دانش و امبدینگ‌ها"""
    conn = get_connection()
    c = conn.cursor()

    # جدول مجموعه‌های دانش (Collections)
    c.execute('''CREATE TABLE IF NOT EXISTS knowledge_collections (
                    id TEXT PRIMARY KEY,
                    username TEXT,
                    title TEXT NOT NULL,
                    description TEXT DEFAULT "",
                    icon TEXT DEFAULT "📚",
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )''')

    # جدول اسناد درون هر مجموعه (Documents)
    c.execute('''CREATE TABLE IF NOT EXISTS knowledge_documents (
                    id TEXT PRIMARY KEY,
                    collection_id TEXT,
                    username TEXT,
                    title TEXT NOT NULL,
                    content TEXT NOT NULL,
                    chunk_count INTEGER DEFAULT 0,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (collection_id) REFERENCES knowledge_collections(id) ON DELETE CASCADE
                )''')

    # جدول قطعات متنی و بردارهای امبدینگ (Chunks & Embeddings)
    c.execute('''CREATE TABLE IF NOT EXISTS knowledge_chunks (
                    id TEXT PRIMARY KEY,
                    document_id TEXT,
                    collection_id TEXT,
                    chunk_index INTEGER,
                    text TEXT NOT NULL,
                    embedding TEXT NOT NULL,
                    FOREIGN KEY (document_id) REFERENCES knowledge_documents(id) ON DELETE CASCADE,
                    FOREIGN KEY (collection_id) REFERENCES knowledge_collections(id) ON DELETE CASCADE
                )''')

    conn.commit()
    conn.close()

# اجرای راه‌اندازی اولیه
init_knowledge_db()


# ==========================================
# 2. موتور تولید امبدینگ و بردار شباهت
# ==========================================
def _local_text_to_vector(text: str, dim: int = 128) -> List[float]:
    """
    تولید بردار معنایی محلی (Hybrid N-Gram + Term Frequency Hashing)
    برای زمانی که کلید امبدینگ خارجی موجود نیست یا برای سرعت حداکثری و بدون هزینه
    """
    cleaned = re.sub(r'[^\w\s]', ' ', text.lower()).strip()
    words = cleaned.split()
    if not words:
        return [0.0] * dim

    vec = [0.0] * dim
    
    # 1. هش کلمات و دوگانه‌ها (Unigram & Bigram)
    tokens = list(words)
    for i in range(len(words) - 1):
        tokens.append(f"{words[i]}_{words[i+1]}")

    for token in tokens:
        h = int(hashlib.md5(token.encode('utf-8')).hexdigest(), 16)
        idx = h % dim
        sign = 1.0 if ((h >> 8) % 2 == 0) else -1.0
        vec[idx] += sign

    # نرمال‌سازی طول بردار (Unit Norm)
    norm = math.sqrt(sum(x * x for x in vec))
    if norm > 0:
        vec = [x / norm for x in vec]

    return vec


def generate_embedding(text: str) -> List[float]:
    """
    تولید امبدینگ متنی؛ در ابتدا تلاش می‌کند از API سرویس فعال استفاده کند،
    در صورت عدم وجود یا خطا، به‌صورت یکپارچه از موتور برداری محلی استفاده می‌کند.
    """
    text = text.strip()
    if not text:
        return [0.0] * 128

    client = get_client()
    provider_key = get_active_provider_key()

    if client:
        try:
            # مدل‌های استاندارد امبدینگ در OpenAI و OpenRouter
            embed_model = "text-embedding-3-small" if provider_key == "openai" else "openai/text-embedding-3-small"
            resp = client.embeddings.create(
                model=embed_model,
                input=text[:4000]
            )
            if resp.data and len(resp.data) > 0:
                return resp.data[0].embedding
        except Exception:
            pass

    # فال‌بک موتور سریع محلی
    return _local_text_to_vector(text, dim=128)


def cosine_similarity(v1: List[float], v2: List[float]) -> float:
    """محاسبه شباهت کسینوسی دو بردار"""
    if not v1 or not v2 or len(v1) != len(v2):
        return 0.0
    dot = sum(a * b for a, b in zip(v1, v2))
    norm1 = math.sqrt(sum(a * a for a in v1))
    norm2 = math.sqrt(sum(b * b for b in v2))
    if norm1 == 0 or norm2 == 0:
        return 0.0
    return dot / (norm1 * norm2)


# ==========================================
# 3. بخش‌بندی متن (Text Chunking)
# ==========================================
def chunk_text(text: str, chunk_size: int = 500, overlap: int = 60) -> List[str]:
    """تقسیم هوشمندانه متن به قطعات قابل هضم با هم‌پوشانی معنایی"""
    cleaned = text.strip()
    if len(cleaned) <= chunk_size:
        return [cleaned] if cleaned else []

    chunks = []
    start = 0
    while start < len(cleaned):
        end = start + chunk_size
        if end >= len(cleaned):
            chunk = cleaned[start:].strip()
            if chunk:
                chunks.append(chunk)
            break

        # تلاش برای شکستن روی نقطه، علامت سوال، خط جدید یا فاصله
        boundary = -1
        for sep in ['\n\n', '\n', '. ', '؟ ', '! ', '، ', ' ']:
            idx = cleaned.rfind(sep, start + chunk_size // 2, end)
            if idx != -1:
                boundary = idx + len(sep)
                break

        if boundary == -1:
            boundary = end

        chunk = cleaned[start:boundary].strip()
        if chunk:
            chunks.append(chunk)

        start = boundary - overlap

    return chunks


# ==========================================
# 4. توابع مدیریت مجموعه‌ها (Collections)
# ==========================================
def create_collection(username: str, title: str, description: str = "", icon: str = "📚") -> Dict[str, Any]:
    """ایجاد مجموعه دانش جدید"""
    conn = get_connection()
    c = conn.cursor()
    col_id = str(uuid.uuid4())
    username = username.strip().lower()
    c.execute(
        "INSERT INTO knowledge_collections (id, username, title, description, icon) VALUES (?, ?, ?, ?, ?)",
        (col_id, username, title.strip(), description.strip(), icon.strip())
    )
    conn.commit()
    conn.close()
    return {
        "id": col_id,
        "title": title.strip(),
        "description": description.strip(),
        "icon": icon.strip(),
        "document_count": 0
    }


def get_user_collections(username: str) -> List[Dict[str, Any]]:
    """دریافت لیست تمام مجموعه‌های دانش کاربر با شمارش اسناد"""
    conn = get_connection()
    c = conn.cursor()
    username = username.strip().lower()
    c.execute("""
        SELECT kc.id, kc.title, kc.description, kc.icon, kc.created_at, COUNT(kd.id) as doc_count
        FROM knowledge_collections kc
        LEFT JOIN knowledge_documents kd ON kc.id = kd.collection_id
        WHERE kc.username = ?
        GROUP BY kc.id
        ORDER BY kc.created_at DESC
    """, (username,))
    rows = c.fetchall()
    conn.close()

    result = []
    for r in rows:
        result.append({
            "id": r[0],
            "title": r[1],
            "description": r[2],
            "icon": r[3] or "📚",
            "created_at": r[4],
            "document_count": r[5]
        })
    return result


def delete_collection(collection_id: str, username: str) -> bool:
    """حذف یک مجموعه دانش به همراه اسناد و قطعات آن"""
    conn = get_connection()
    c = conn.cursor()
    username = username.strip().lower()
    # حذف چانک‌ها
    c.execute("DELETE FROM knowledge_chunks WHERE collection_id = ?", (collection_id,))
    # حذف داکیومنت‌ها
    c.execute("DELETE FROM knowledge_documents WHERE collection_id = ?", (collection_id,))
    # حذف مجموعه
    c.execute("DELETE FROM knowledge_collections WHERE id = ? AND username = ?", (collection_id, username))
    affected = c.rowcount
    conn.commit()
    conn.close()
    return affected > 0


# ==========================================
# 5. توابع مدیریت اسناد و ایندکس برداری
# ==========================================
def add_document_to_collection(collection_id: str, username: str, title: str, content: str) -> Dict[str, Any]:
    """
    افزودن سند به پایگاه دانش، قطعه‌بندی خودکار، تولید بردارها و ذخیره‌سازی
    """
    conn = get_connection()
    c = conn.cursor()
    username = username.strip().lower()

    # بررسی صحت دسترسی به مجموعه
    c.execute("SELECT id FROM knowledge_collections WHERE id = ? AND username = ?", (collection_id, username))
    if not c.fetchone():
        conn.close()
        raise ValueError("مجموعه دانش یافت نشد یا دسترسی غیرمجاز است.")

    doc_id = str(uuid.uuid4())
    chunks = chunk_text(content, chunk_size=450, overlap=50)

    c.execute(
        "INSERT INTO knowledge_documents (id, collection_id, username, title, content, chunk_count) VALUES (?, ?, ?, ?, ?, ?)",
        (doc_id, collection_id, username, title.strip(), content, len(chunks))
    )

    # ایجاد و ذخیره امبدینگ هر قطعه
    for idx, chunk in enumerate(chunks):
        chunk_id = str(uuid.uuid4())
        emb = generate_embedding(chunk)
        emb_json = json.dumps(emb)
        c.execute(
            "INSERT INTO knowledge_chunks (id, document_id, collection_id, chunk_index, text, embedding) VALUES (?, ?, ?, ?, ?, ?)",
            (chunk_id, doc_id, collection_id, idx, chunk, emb_json)
        )

    conn.commit()
    conn.close()

    return {
        "id": doc_id,
        "title": title.strip(),
        "chunk_count": len(chunks)
    }


def get_collection_documents(collection_id: str, username: str) -> List[Dict[str, Any]]:
    """دریافت لیست اسناد یک مجموعه"""
    conn = get_connection()
    c = conn.cursor()
    username = username.strip().lower()
    c.execute("""
        SELECT id, title, chunk_count, created_at, length(content) as content_len
        FROM knowledge_documents
        WHERE collection_id = ? AND username = ?
        ORDER BY created_at DESC
    """, (collection_id, username))
    rows = c.fetchall()
    conn.close()

    return [{
        "id": r[0],
        "title": r[1],
        "chunk_count": r[2],
        "created_at": r[3],
        "length": r[4]
    } for r in rows]


def delete_document(document_id: str, username: str) -> bool:
    """حذف یک سند و امبدینگ‌های آن"""
    conn = get_connection()
    c = conn.cursor()
    username = username.strip().lower()
    c.execute("DELETE FROM knowledge_chunks WHERE document_id = ?", (document_id,))
    c.execute("DELETE FROM knowledge_documents WHERE id = ? AND username = ?", (document_id, username))
    affected = c.rowcount
    conn.commit()
    conn.close()
    return affected > 0


# ==========================================
# 6. جستجوی معنایی و بازیابی متنی (RAG Search)
# ==========================================
def search_knowledge_collection(collection_id: str, query: str, top_k: int = 4) -> List[Dict[str, Any]]:
    """
    جستجوی معنایی در یک مجموعه دانش با مقایسه بردار سوال با تمام قطعات سند
    """
    if not query.strip() or not collection_id:
        return []

    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        SELECT kc.text, kc.embedding, kd.title, kc.chunk_index
        FROM knowledge_chunks kc
        JOIN knowledge_documents kd ON kc.document_id = kd.id
        WHERE kc.collection_id = ?
    """, (collection_id,))
    rows = c.fetchall()
    conn.close()

    if not rows:
        return []

    query_vec = generate_embedding(query)

    scored_chunks = []
    for text, emb_json, doc_title, chunk_idx in rows:
        try:
            chunk_vec = json.loads(emb_json)
            score = cosine_similarity(query_vec, chunk_vec)
            scored_chunks.append({
                "title": doc_title,
                "text": text,
                "chunk_index": chunk_idx,
                "score": round(score, 4)
            })
        except Exception:
            continue

    # مرتب‌سازی بر اساس بالاترین میزان شباهت
    scored_chunks.sort(key=lambda x: x["score"], reverse=True)
    return scored_chunks[:top_k]
