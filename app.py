import os
import streamlit as st
import chromadb
from chromadb import Documents, EmbeddingFunction, Embeddings
from zhipuai import ZhipuAI
import pdfplumber
from dotenv import load_dotenv

load_dotenv()

ZHIPUAI_API_KEY = os.getenv("ZHIPUAI_API_KEY")
client_zhipu = ZhipuAI(api_key=ZHIPUAI_API_KEY)

# 智谱嵌入函数
class ZhipuEmbeddingFunction(EmbeddingFunction):
    def __call__(self, input: Documents) -> Embeddings:
        embeddings = []
        for text in input:
            response = client_zhipu.embeddings.create(
                model="embedding-3",
                input=text
            )
            embeddings.append(response.data[0].embedding)
        return embeddings

# 初始化ChromaDB
@st.cache_resource
def init_collection():
    chroma_client = chromadb.Client()
    embedding_fn = ZhipuEmbeddingFunction()
    return chroma_client.get_or_create_collection(
        name="contracts",
        embedding_function=embedding_fn
    )

collection = init_collection()

# 提取PDF
def extract_pdf_chunks(pdf_path):
    chunks = []
    with pdfplumber.open(pdf_path) as pdf:
        for i, page in enumerate(pdf.pages):
            text = page.extract_text()
            if not text:
                continue
            chunks.append({
                "text": text,
                "page": i + 1,
                "source": pdf_path
            })
    return chunks

# 导入PDF
def index_pdf(pdf_path):
    chunks = extract_pdf_chunks(pdf_path)
    collection.add(
        documents=[c["text"] for c in chunks],
        metadatas=[{"page": c["page"], "source": c["source"]} for c in chunks],
        ids=[f"{pdf_path}_page_{c['page']}" for c in chunks]
    )
    return len(chunks)

# 查询
def query_contract(question):
    results = collection.query(
        query_texts=[question],
        n_results=3
    )
    
    context = ""
    sources = []
    for doc, meta in zip(results["documents"][0], results["metadatas"][0]):
        context += f"\n[第{meta['page']}页]\n{doc}\n"
        sources.append(f"第{meta['page']}页")
    
    response = client_zhipu.chat.completions.create(
        model="glm-4-flash",
        messages=[
            {
                "role": "system",
                "content": "你是一个合同分析助手，根据提供的合同内容回答问题，回答要简洁准确，并说明信息来自哪一页。"
            },
            {
                "role": "user",
                "content": f"合同内容：\n{context}\n\n问题：{question}"
            }
        ]
    )
    
    return response.choices[0].message.content, sources

# ===== Streamlit界面 =====
st.title("📄 合同智能查询系统")

# 上传PDF
st.sidebar.header("上传合同")
uploaded_file = st.sidebar.file_uploader("选择PDF文件", type="pdf")

if uploaded_file:
    # 保存到本地
    with open(uploaded_file.name, "wb") as f:
        f.write(uploaded_file.getbuffer())
    
    if st.sidebar.button("导入合同"):
        with st.spinner("正在导入..."):
            count = index_pdf(uploaded_file.name)
            st.sidebar.success(f"已导入 {count} 个chunk")

# 查询区域
st.header("提问")
question = st.text_input("输入你的问题", placeholder="例如：What are the payment terms?")

if st.button("查询") and question:
    with st.spinner("查询中..."):
        answer, sources = query_contract(question)
    
    st.subheader("答案")
    st.write(answer)
    
    st.caption(f"来源：{', '.join(sources)}")