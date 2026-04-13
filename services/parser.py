# 把PDF 转化为纯文本
import os
from typing import List, Dict

import pdfplumber
from docx import Document

from services.text_normalizer import normalize_pdf_text, normalize_plain_text


def extract_pdf_pages(file_path: str) -> List[Dict]:
    raw_pages = []

    with pdfplumber.open(file_path) as pdf:
        for i, page in enumerate(pdf.pages):
            text = page.extract_text()
            if not text:
                continue
            raw_pages.append({"page": i + 1, "text": text})

    all_page_texts = [p["text"] for p in raw_pages]

    pages = []
    for p in raw_pages:
        pages.append(
            {
                "page": p["page"],
                "text": p["text"],
                "normalized_text": normalize_pdf_text(
                    p["text"], all_page_texts=all_page_texts
                ),
                "file_type": "pdf",
            }
        )

    return pages


def extract_txt_pages(file_path: str) -> List[Dict]:
    with open(file_path, "r", encoding="utf-8") as f:
        text = f.read()

    return [
        {
            "page": 1,
            "text": text,
            "normalized_text": normalize_plain_text(text),
            "file_type": "txt",
        }
    ]


def extract_docx_pages(file_path: str) -> List[Dict]:
    doc = Document(file_path)
    paragraphs = [p.text.strip() for p in doc.paragraphs if p.text.strip()]
    text = "\n\n".join(paragraphs)

    return [
        {
            "page": 1,
            "text": text,
            "normalized_text": normalize_plain_text(text),
            "file_type": "docx",
        }
    ]


def extract_document_pages(file_path: str) -> List[Dict]:
    ext = os.path.splitext(file_path)[1].lower()

    if ext == ".pdf":
        return extract_pdf_pages(file_path)
    if ext == ".txt":
        return extract_txt_pages(file_path)
    if ext == ".docx":
        return extract_docx_pages(file_path)

    raise ValueError(f"Unsupported file type: {ext}")
