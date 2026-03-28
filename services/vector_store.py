# 向量存储与检索
import streamlit as st
import chromadb
from collections import defaultdict
from services.embeddings import ZhipuEmbeddingFunction


@st.cache_resource
def init_collection():
    chroma_client = chromadb.Client()
    embedding_fn = ZhipuEmbeddingFunction()
    return chroma_client.get_or_create_collection(
        name="contracts", embedding_function=embedding_fn
    )


def delete_document_by_source(source: str):
    collection = init_collection()
    collection.delete(where={"source": source})


def list_indexed_documents():
    collection = init_collection()
    data = collection.get(include=["metadatas"])

    metadatas = data.get("metadatas", [])
    if not metadatas:
        return []

    grouped = defaultdict(lambda: {"chunks": 0, "pages": set()})

    for meta in metadatas:
        source = meta.get("source", "unknown")
        grouped[source]["chunks"] += 1
        if "page" in meta:
            grouped[source]["pages"].add(meta["page"])

    documents = []
    for source, info in grouped.items():
        documents.append(
            {
                "source": source,
                "chunk_count": info["chunks"],
                "page_count": len(info["pages"]),
            }
        )

    documents.sort(key=lambda x: x["source"])
    return documents
