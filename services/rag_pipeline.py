import os
from zhipuai import ZhipuAI
from dotenv import load_dotenv

from services.parser import extract_document_pages
from services.chunking import build_page_chunks
from services.vector_store import (
    init_collection,
    delete_document_by_source,
    get_all_chunks,
)
from services.document_router import detect_doc_category, choose_chunk_strategy
from services.bm25_index import rebuild_bm25_index
from services.retrieval import hybrid_search

load_dotenv()

ZHIPUAI_API_KEY = os.getenv("ZHIPUAI_API_KEY")
client_zhipu = ZhipuAI(api_key=ZHIPUAI_API_KEY)


def _sync_bm25_index():
    """从向量库全量重建 BM25 内存索引。"""
    documents, metadatas = get_all_chunks()
    rebuild_bm25_index(documents, metadatas)


def index_document(file_path: str, source_name: str = None):
    collection = init_collection()
    pages = extract_document_pages(file_path)

    if not pages:
        return 0

    display_name = source_name or os.path.basename(file_path)
    file_type = pages[0].get("file_type") or os.path.splitext(file_path)[1].lstrip(".").lower() or "unknown"
    doc_category = detect_doc_category(file_type=file_type, pages=pages)
    chunk_strategy = choose_chunk_strategy(doc_category)

    delete_document_by_source(display_name)

    all_chunks = []

    for page in pages:
        page["source"] = display_name

        page_chunks = build_page_chunks(
            page=page,
            chunk_strategy=chunk_strategy,
        )
        all_chunks.extend(page_chunks)

    all_chunks = [c for c in all_chunks if c["text"].strip()]

    if not all_chunks:
        return 0

    collection.add(
        documents=[c["text"] for c in all_chunks],
        metadatas=[
            {
                "page": c["page"],
                "source": c["source"],
                "chunk_index": c["chunk_index"],
                "doc_category": doc_category,
                "chunk_strategy": chunk_strategy,
                "file_type": file_type,
            }
            for c in all_chunks
        ],
        ids=[
            f"{c['source']}_page_{c['page']}_chunk_{c['chunk_index']}"
            for c in all_chunks
        ],
    )

    _sync_bm25_index()

    return len(all_chunks)


def query_contract(question: str, top_k: int = 3):
    retrieved_chunks = hybrid_search(question, top_k=top_k)

    if not retrieved_chunks:
        return "文档中未找到相关信息。", [], []

    MAX_CONTEXT_CHARS = 3000
    context_parts = []
    sources = []
    used_chunks = []
    current_length = 0

    for chunk in retrieved_chunks:
        source_text = (
            f"{chunk['source']} - 第{chunk['page']}页 - chunk {chunk['chunk_index']}"
        )
        part = f"[文件: {chunk['source']} | 第{chunk['page']}页 | chunk {chunk['chunk_index']}]\n{chunk['text']}"

        if current_length + len(part) > MAX_CONTEXT_CHARS:
            chunk["in_context"] = False
            used_chunks.append(chunk)
            continue

        chunk["in_context"] = True
        context_parts.append(part)
        sources.append(source_text)
        used_chunks.append(chunk)
        current_length += len(part)

    if not context_parts:
        return "文档中未找到相关信息。", [], used_chunks

    context = "\n\n".join(context_parts)

    system_prompt = """
你是一个严格基于文档上下文进行回答的问答助手。

规则：
1. 只能根据我提供的文档上下文回答问题。
2. 如果答案不能从文档上下文中直接找到，请明确回答：文档中未找到相关信息。
3. 不要使用你自己的常识、经验、外部知识或猜测来补充答案。
4. 不要把不确定的信息说成确定事实。
5. 回答尽量简洁、准确。
6. 回答末尾尽量附上引用来源。
"""

    user_prompt = f"""
请仅依据以下文档上下文回答问题。

文档上下文：
{context}

问题：
{question}

请按以下格式回答：
答案：<你的回答>
来源：<来源列表；如果未找到则写 无>

要求：
- 如果上下文不足，请回答：文档中未找到相关信息。
- 不要猜测。
- 不要补充上下文之外的知识。
"""

    response = client_zhipu.chat.completions.create(
        model="glm-4-flash",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    )

    return response.choices[0].message.content, sources, used_chunks
