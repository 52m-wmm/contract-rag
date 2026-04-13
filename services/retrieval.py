# 检索模块：dense / bm25 / hybrid (RRF)
from typing import List, Dict

from services.vector_store import init_collection
from services.bm25_index import bm25_search


def dense_search(query: str, top_k: int = 5) -> List[Dict]:
    """向量 dense 检索。"""
    collection = init_collection()
    results = collection.query(query_texts=[query], n_results=top_k)

    documents = results.get("documents", [[]])[0]
    metadatas = results.get("metadatas", [[]])[0]
    distances = results.get("distances", [[]])[0]

    hits = []
    for rank, (doc, meta, dist) in enumerate(zip(documents, metadatas, distances)):
        if not doc or not doc.strip():
            continue
        hits.append(
            {
                "text": doc,
                "source": meta.get("source", ""),
                "page": meta.get("page", 0),
                "chunk_index": meta.get("chunk_index", 0),
                "file_type": meta.get("file_type", ""),
                "doc_category": meta.get("doc_category", ""),
                "chunk_strategy": meta.get("chunk_strategy", ""),
                "dense_score": float(dist),
                "dense_rank": rank + 1,
            }
        )
    return hits


def rrf_fuse(
    dense_results: List[Dict],
    bm25_results: List[Dict],
    k: int = 60,
    top_k: int = 5,
) -> List[Dict]:
    """Reciprocal Rank Fusion：融合 dense 和 BM25 结果。"""
    score_map: Dict[str, Dict] = {}

    def _chunk_key(item: Dict) -> str:
        return f"{item['source']}|{item['page']}|{item['chunk_index']}"

    for item in dense_results:
        key = _chunk_key(item)
        if key not in score_map:
            score_map[key] = {**item, "dense_score": 0.0, "dense_rank": 0,
                              "bm25_score": 0.0, "bm25_rank": 0, "rrf_score": 0.0}
        score_map[key]["dense_score"] = item.get("dense_score", 0.0)
        score_map[key]["dense_rank"] = item.get("dense_rank", 0)
        score_map[key]["rrf_score"] += 1.0 / (k + item.get("dense_rank", 999))

    for item in bm25_results:
        key = _chunk_key(item)
        if key not in score_map:
            score_map[key] = {**item, "dense_score": 0.0, "dense_rank": 0,
                              "bm25_score": 0.0, "bm25_rank": 0, "rrf_score": 0.0}
        score_map[key]["bm25_score"] = item.get("bm25_score", 0.0)
        score_map[key]["bm25_rank"] = item.get("bm25_rank", 0)
        score_map[key]["rrf_score"] += 1.0 / (k + item.get("bm25_rank", 999))

    fused = sorted(score_map.values(), key=lambda x: x["rrf_score"], reverse=True)

    for rank, item in enumerate(fused):
        item["fused_rank"] = rank + 1

    return fused[:top_k]


def hybrid_search(query: str, top_k: int = 5) -> List[Dict]:
    """默认混合检索入口。"""
    dense_results = dense_search(query, top_k=top_k * 2)
    bm25_results = bm25_search(query, top_k=top_k * 2)
    return rrf_fuse(dense_results, bm25_results, top_k=top_k)