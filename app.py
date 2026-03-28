import os
import tempfile
import streamlit as st

from services.rag_pipeline import index_document, query_contract
from services.vector_store import list_indexed_documents, delete_document_by_source

st.set_page_config(page_title="AI 文档问答系统", layout="wide")

st.title("📄 AI 文档问答系统")

# =========================
# 上传文档
# =========================
st.sidebar.header("上传文档")

uploaded_file = st.sidebar.file_uploader("选择文件", type=["pdf", "txt", "docx"])

if uploaded_file:
    if st.sidebar.button("导入文档"):
        with tempfile.NamedTemporaryFile(
            delete=False, suffix=os.path.splitext(uploaded_file.name)[1]
        ) as tmp_file:
            tmp_file.write(uploaded_file.getbuffer())
            temp_path = tmp_file.name

        with st.spinner("正在导入并建立索引..."):
            count = index_document(temp_path, source_name=uploaded_file.name)

        st.sidebar.success(f"已导入 {count} 个 chunks")


# =========================
# 检索参数
# =========================
st.sidebar.header("检索参数")

top_k = st.sidebar.slider(
    "top_k（检索片段数）",
    min_value=1,
    max_value=8,
    value=3,
    help="从向量库中取最相关的几个文本块",
)


# =========================
# 文档列表
# =========================
st.sidebar.header("已导入文档")

documents = list_indexed_documents()

if not documents:
    st.sidebar.caption("暂无已导入文档")
else:
    for doc in documents:
        st.sidebar.markdown(
            f"**{doc['source']}**\n\n"
            f"- pages: {doc['page_count']}\n"
            f"- chunks: {doc['chunk_count']}"
        )

        if st.sidebar.button(f"删除 {doc['source']}", key=f"delete_{doc['source']}"):
            delete_document_by_source(doc["source"])
            st.sidebar.success(f"已删除 {doc['source']}")
            st.rerun()


# =========================
# 问答区域
# =========================
st.header("提问")

question = st.text_input("输入你的问题", placeholder="例如：付款条款是什么？")

if st.button("查询"):
    if not question.strip():
        st.warning("请输入问题")
    else:
        with st.spinner("查询中..."):
            answer, sources, retrieved_chunks = query_contract(question, top_k=top_k)

        st.subheader("🧠 答案")
        st.write(answer)

        if sources:
            st.subheader("📚 来源")
            for source in sources:
                st.write(f"- {source}")
        else:
            st.caption("无引用来源")

        st.subheader("🔍 实际召回的文本块（调试）")
        if not retrieved_chunks:
            st.write("没有召回任何 chunk")
        else:
            for chunk in retrieved_chunks:
                title = (
                    f"{chunk['source']} | 第{chunk['page']}页 | chunk {chunk['chunk_index']} "
                    f"| {chunk['file_type']} | {chunk['doc_category']} | {chunk['chunk_strategy']}"
                )
                with st.expander(title):
                    st.write(chunk["text"])
