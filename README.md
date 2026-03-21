# 合同智能查询系统

基于 RAG 架构的合同分析工具，上传 PDF 合同后可用自然语言直接提问，返回答案及来源页码。

## 技术栈
- 向量检索：ChromaDB + 智谱 Embedding
- 生成模型：GLM-4-flash
- 界面：Streamlit

## 功能
- PDF 合同上传与解析
- 自然语言查询合同内容
- 返回答案及来源页码定位

## 快速开始

1. 安装依赖
pip install -r requirements.txt

2. 配置 API Key
复制 .env.example 为 .env，填入智谱 API Key

3. 启动
streamlit run app.py

## 后续规划
- 替换为 OpenAI Embeddings + pgvector（生产环境）
- FastAPI 后端 + 前端界面
- Google Drive 自动同步
- 合同到期自动提醒