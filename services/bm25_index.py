# 基于 rank_bm25 的内存 BM25 索引
import re
from typing import List, Dict, Optional

from rank_bm25 import BM25Okapi


_bm25_instance: Optional[BM25Okapi] = None
_bm25_corpus_docs: List[str] = []
_bm25_corpus_metas: List[Dict] = []


def _tokenize(text: str) -> List[str]:
    """简单分词：按空白 + 标点切分，转小写。"""
    return [t for t in re.split(r"[\s\W]+", text.lower()) if t]


def rebuild_bm25_index(documents: List[str], metadatas: List[Dict]):
    """用当前向量库中的全量 chunk 重建 BM25 索引。"""
    global _bm25_instance, _bm25_corpus_docs, _bm25_corpus_metas

    _bm25_corpus_docs = list(documents)
    _bm25_corpus_metas = list(metadatas)

    tokenized = [_tokenize(doc) for doc in _bm25_corpus_docs]
    _bm25_instance = BM25Okapi(tokenized) if tokenized else None


def bm25_search(query: str, top_k: int = 5) -> List[Dict]:
    """BM25 稀疏检索，返回 top_k 结果。"""
    if _bm25_instance is None or not _bm25_corpus_docs:
        return []

    tokenized_query = _tokenize(query)
    if not tokenized_query:
        return []

    scores = _bm25_instance.get_scores(tokenized_query)

    scored_indices = sorted(
        range(len(scores)), key=lambda i: scores[i], reverse=True
    )[:top_k]

    results = []
    for rank, idx in enumerate(scored_indices):
        if scores[idx] <= 0:
            continue
        meta = _bm25_corpus_metas[idx] if idx < len(_bm25_corpus_metas) else {}
        results.append(
            {
                "text": _bm25_corpus_docs[idx],
                "source": meta.get("source", ""),
                "page": meta.get("page", 0),
                "chunk_index": meta.get("chunk_index", 0),
                "file_type": meta.get("file_type", ""),
                "doc_category": meta.get("doc_category", ""),
                "chunk_strategy": meta.get("chunk_strategy", ""),
                "bm25_score": float(scores[idx]),
                "bm25_rank": rank + 1,
            }
        )

    return results


def is_index_ready() -> bool:
    return _bm25_instance is not None and len(_bm25_corpus_docs) > 0
