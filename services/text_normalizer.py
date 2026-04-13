# PDF 文本标准化：合并断行、统一空白、去除页眉页脚噪声
import re
from typing import List


def normalize_pdf_text(text: str, all_page_texts: List[str] = None) -> str:
    """将 PDF 提取的原始文本清洗为适合检索和切块的标准化文本。

    Args:
        text: 单页原始文本。
        all_page_texts: 所有页的原始文本列表，用于页眉页脚检测。
    """
    if not text:
        return ""

    text = _strip_header_footer(text, all_page_texts)
    text = _normalize_whitespace(text)
    text = _merge_broken_lines(text)
    text = _collapse_blank_lines(text)

    return text.strip()


def normalize_plain_text(text: str) -> str:
    """对 TXT / DOCX 做轻度清洗。"""
    if not text:
        return ""

    text = _normalize_whitespace(text)
    text = _collapse_blank_lines(text)
    return text.strip()


# ── 内部工具函数 ─────────────────────────────────────────────────

def _normalize_whitespace(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"\t", " ", text)
    text = re.sub(r"[^\S\n]+", " ", text)
    return text


def _merge_broken_lines(text: str) -> str:
    """合并 PDF 中常见的异常断行（行尾非标点、下行首字母小写等）。"""
    lines = text.split("\n")
    merged = []
    for line in lines:
        stripped = line.strip()
        if not stripped:
            merged.append("")
            continue

        if (
            merged
            and merged[-1]
            and not merged[-1].endswith((".", "。", "!", "！", "?", "？", ":", "：", ";", "；"))
            and not re.match(r"^[A-Z\d（(【\[]", stripped)
            and not re.match(r"^(Section|Article|ARTICLE|第)", stripped)
        ):
            merged[-1] = merged[-1] + " " + stripped
        else:
            merged.append(stripped)

    return "\n".join(merged)


def _collapse_blank_lines(text: str) -> str:
    return re.sub(r"\n{3,}", "\n\n", text)


def _strip_header_footer(text: str, all_page_texts: List[str] = None) -> str:
    """用轻量启发式去除重复的页眉页脚行。

    策略：如果某行在 ≥50% 的页面中出现，且长度较短，判定为页眉/页脚并移除。
    """
    if not all_page_texts or len(all_page_texts) < 3:
        return text

    line_counts = {}
    for pt in all_page_texts:
        seen = set()
        for line in pt.split("\n"):
            line_stripped = line.strip()
            if line_stripped and len(line_stripped) < 80 and line_stripped not in seen:
                seen.add(line_stripped)
                line_counts[line_stripped] = line_counts.get(line_stripped, 0) + 1

    threshold = len(all_page_texts) * 0.5
    noise_lines = {l for l, c in line_counts.items() if c >= threshold and len(l) < 80}

    if not noise_lines:
        return text

    filtered = []
    for line in text.split("\n"):
        if line.strip() not in noise_lines:
            filtered.append(line)

    return "\n".join(filtered)
