import os
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
chroma_client = chromadb.Client()
embedding_fn = ZhipuEmbeddingFunction()
collection = chroma_client.get_or_create_collection(
    name="contracts",
    embedding_function=embedding_fn
)

# 1. 提取PDF
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

# 2. 导入PDF到ChromaDB
def index_pdf(pdf_path):
    chunks = extract_pdf_chunks(pdf_path)
    collection.add(
        documents=[c["text"] for c in chunks],
        metadatas=[{"page": c["page"], "source": c["source"]} for c in chunks],
        ids=[f"{pdf_path}_page_{c['page']}" for c in chunks]
    )
    print(f"已导入 {len(chunks)} 个chunk")

# 3. 查询并用智谱生成答案
def query_contract(question):
    # 检索相关chunk
    results = collection.query(
        query_texts=[question],
        n_results=3
    )
    
    # 拼接上下文
    context = ""
    sources = []
    for doc, meta in zip(results["documents"][0], results["metadatas"][0]):
        context += f"\n[第{meta['page']}页]\n{doc}\n"
        sources.append(f"第{meta['page']}页")
    
    # 用智谱生成答案
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
    
    answer = response.choices[0].message.content
    print(f"\n问题：{question}")
    print(f"答案：{answer}")
    print(f"来源：{', '.join(sources)}")

# 主程序
if __name__ == "__main__":
    # 导入合同
    index_pdf("合同.pdf")
    
    # 测试问题
    query_contract("What is the lease term?")
    query_contract("What are the payment terms?")