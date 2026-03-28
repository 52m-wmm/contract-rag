# 判断文件类型，结构
from typing import List, Dict


def detect_doc_category(file_type: str, pages: List[Dict]) -> str:
    sample_text = "\n".join([p.get("text", "") for p in pages[:2]]).lower()

    if file_type == "pdf":
        structured_signals = 0

        keywords = [
            "section",
            "article",
            "lessor",
            "government",
            "template",
            "lease no.",
            "rev (",
            "table of contents",
        ]

        for kw in keywords:
            if kw in sample_text:
                structured_signals += 1

        lines = [line.strip() for line in sample_text.split("\n") if line.strip()]
        short_lines = [line for line in lines if len(line) < 60]

        if len(short_lines) > 20:
            structured_signals += 1

        if structured_signals >= 2:
            return "structured_pdf"

        return "natural_pdf"

    if file_type in ["txt", "docx"]:
        return "natural_text"

    return "default"


def choose_chunk_strategy(doc_category: str) -> str:
    if doc_category == "structured_pdf":
        return "page_fixed"

    if doc_category in ["natural_pdf", "natural_text"]:
        return "paragraph"

    return "paragraph"
