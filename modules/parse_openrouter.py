# modules/parse_openrouter.py
"""
ابزار استخراج و تحلیل مدل‌های OpenRouter از فایل Openrouter.txt
"""

import os
import re
import json

def parse_openrouter_file(file_path="Openrouter.txt"):
    if not os.path.exists(file_path):
        return []

    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        raw = f.read()

    blocks = raw.split("Favicon for")
    models = []

    for b in blocks[1:]:
        lines = [l.strip() for l in b.strip().split("\n") if l.strip()]
        if not lines:
            continue

        vendor_slug = lines[0].lower().strip()
        title = lines[1] if len(lines) > 1 else vendor_slug
        
        # Clean title
        clean_title = title
        if ":" in title:
            clean_title = title.split(":", 1)[1].strip()

        # Find description
        desc = ""
        for line in lines[2:]:
            if line.startswith("by ") or line.startswith("$") or "context" in line.lower() or "tokens" in line.lower():
                continue
            if len(line) > 25 and not desc:
                desc = line
                break

        context_str = "128K context"
        inp_price = 0.0
        out_price = 0.0
        is_free = "free" in title.lower() or "(free)" in b.lower()

        for l in lines:
            if "context" in l.lower() and not l.startswith("by "):
                context_str = l
            m_in = re.search(r"\$([0-9.]+)/M input", l)
            if m_in:
                inp_price = float(m_in.group(1))
            m_out = re.search(r"\$([0-9.]+)/M output", l)
            if m_out:
                out_price = float(m_out.group(1))
            m_img = re.search(r"\$([0-9.]+)/(?:image|megapixel)", l)
            if m_img:
                out_price = float(m_img.group(1))
                if inp_price == 0.0:
                    inp_price = out_price

        # Determine type
        low_b = b.lower()
        if "image" in low_b or "megapixel" in low_b or "flux" in low_b or "seedream" in low_b or "riverflow" in low_b or "dall-e" in low_b:
            m_type = "image"
        elif "audio" in low_b or "speech" in low_b or "voice" in low_b or "whisper" in low_b or "tts" in low_b:
            m_type = "audio"
        elif "embed" in low_b or "rerank" in low_b:
            m_type = "embedding"
        else:
            m_type = "chat"

        # Generate standard OpenRouter model ID
        # e.g., google/gemini-2.5-flash or nvidia/nemotron-3-ultra
        slug_name = re.sub(r"[^a-zA-Z0-9-.]+", "-", clean_title.lower()).strip("-")
        slug_name = slug_name.replace("-free", "")
        model_id = f"{vendor_slug}/{slug_name}"

        models.append({
            "id": model_id,
            "name": title,
            "vendor": vendor_slug,
            "description": desc or clean_title,
            "context": context_str,
            "input_price": inp_price,
            "output_price": out_price,
            "is_free": is_free,
            "type": m_type
        })

    return models

if __name__ == "__main__":
    mods = parse_openrouter_file()
    print(f"Total parsed OpenRouter models: {len(mods)}")
    # Save to json
    with open("data/openrouter_models.json", "w", encoding="utf-8") as f:
        json.dump(mods, f, ensure_ascii=False, indent=2)
    print("Saved to data/openrouter_models.json successfully!")
