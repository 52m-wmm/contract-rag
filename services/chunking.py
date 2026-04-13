# 文本切块
import re
from typing import List, Dict


def clean_text(text: str) -> str:
    if not text:
        return ""

    text = text.replace("\r\n", "\n").replace("\r", "\n")
    lines = [line.strip() for line in text.split("\n")]

    cleaned_lines = []
    previous_blank = False

    for line in lines:
        if not line:
            if not previous_blank:
                cleaned_lines.append("")
            previous_blank = True
        else:
            line = re.sub(r"\s+", " ", line)
            cleaned_lines.append(line)
            previous_blank = False

    return "\n".join(cleaned_lines).strip()


def split_long_text(
    text: str, max_chunk_chars: int = 800, overlap: int = 100
) -> List[str]:
    if len(text) <= max_chunk_chars:
        return [text]

    chunks = []
    start = 0
    text_len = len(text)

    while start < text_len:
        end = min(start + max_chunk_chars, text_len)
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)

        if end == text_len:
            break

        start = max(end - overlap, start + 1)

    return chunks


def paragraph_chunk_text(
    text: str,
    min_chunk_chars: int = 180,
    max_chunk_chars: int = 800,
    overlap: int = 100,
) -> List[str]:
    text = clean_text(text)
    if not text:
        return []

    raw_paragraphs = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]

    merged_paragraphs = []
    buffer = ""

    for para in raw_paragraphs:
        if not buffer:
            buffer = para
            continue

        if len(buffer) < min_chunk_chars:
            buffer = f"{buffer}\n{para}"
        else:
            merged_paragraphs.append(buffer)
            buffer = para

    if buffer:
        merged_paragraphs.append(buffer)

    final_chunks = []

    for para in merged_paragraphs:
        if len(para) <= max_chunk_chars:
            final_chunks.append(para)
        else:
            final_chunks.extend(
                split_long_text(
                    para,
                    max_chunk_chars=max_chunk_chars,
                    overlap=overlap,
                )
            )

    return final_chunks


def page_fixed_chunk_text(
    text: str,
    page_chunk_threshold: int = 1000,
    chunk_size: int = 800,
    overlap: int = 100,
) -> List[str]:
    text = clean_text(text)
    if not text:
        return []

    if len(text) <= page_chunk_threshold:
        return [text]

    return split_long_text(
        text,
        max_chunk_chars=chunk_size,
        overlap=overlap,
    )


def build_page_chunks(
    page: Dict,
    chunk_strategy: str = "paragraph",
) -> List[Dict]:
    page_text = page.get("normalized_text") or page.get("text", "")
    source_file = page.get("source", "unknown")
    page_number = page.get("page", 1)

    if chunk_strategy == "page_fixed":
        chunks = page_fixed_chunk_text(
            page_text,
            page_chunk_threshold=1000,
            chunk_size=800,
            overlap=100,
        )
    else:
        chunks = paragraph_chunk_text(
            page_text,
            min_chunk_chars=180,
            max_chunk_chars=800,
            overlap=100,
        )

    results = []
    for idx, chunk in enumerate(chunks):
        if chunk.strip():
            results.append(
                {
                    "source": source_file,
                    "page": page_number,
                    "chunk_index": idx,
                    "text": chunk,
                }
            )

    return results
