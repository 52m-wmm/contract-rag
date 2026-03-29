AI 文档问答系统（RAG）README

📄 AI 文档问答系统（RAG）

一个基于 RAG（Retrieval-Augmented Generation）的文档问答系统原型，支持多格式文档接入、向量检索、文档管理、引用溯源，以及面向不同文档结构的切分策略选择。

当前版本重点关注：
多格式文档解析
RAG 基础链路工程化
文档管理与重建索引
检索调试与问题定位
结构化 PDF 与自然语言文档的差异化处理

---

🚀 功能特性

支持 PDF / TXT / DOCX 文档上传
支持文档解析、切块、向量化、检索、问答全流程
支持文档列表展示
支持按文档删除索引
支持重复上传同名文档时自动重建索引
支持 top_k 可调
支持显示实际召回的文本块，便于调试检索效果
支持基于文档结构选择不同 chunk 策略
支持基础防幻觉约束（仅根据上下文回答，找不到则拒答）

---

🧠 项目背景

这个项目最初是一个简单的合同问答 RAG Demo，后续逐步升级为一个更具工程结构的文档问答系统原型。

在迭代过程中，重点不是只让模型“答出来”，而是让系统具备：

更清晰的模块划分
更可控的文档接入流程
更可解释的检索结果
更真实的 RAG 调试能力

---

🏗️ 系统架构

用户操作（Streamlit UI）
        ↓
app.py（界面层）
        ↓
rag_pipeline（流程编排）
        ↓
parser → document_router → chunking → vector_store → LLM

---

📂 项目结构

rag/
├── app.py
├── services/
│   ├── parser.py
│   ├── document_router.py
│   ├── chunking.py
│   ├── embeddings.py
│   ├── vector_store.py
│   └── rag_pipeline.py
├── requirements.txt
└── README.md

---

🔧 模块说明

1. app.py
负责用户界面交互：

上传文档
查看已导入文档
删除文档索引
输入问题
展示答案
展示引用来源
展示召回的文本块（调试）

该层只负责 UI，不承载核心业务逻辑。

---

2. parser.py
负责文档解析，将不同类型文档统一转换为标准结构。

当前支持：
PDF：按页提取文本
TXT：整体读取
DOCX：按段落提取并合并

统一输出格式示例：

{
    "page": 1,
    "text": "...",
    "source": "example.pdf",
    "file_type": "pdf"
}

---

3. document_router.py
负责对文档进行轻量判断，并根据文档结构选择更合适的 chunk 策略。

当前分类思路：
structured_pdf：结构化 PDF（合同模板、表格型文档、政府模板等）
natural_pdf：自然语言结构较清晰的 PDF
natural_text：TXT / DOCX 等自然文本

对应策略：
structured_pdf → page_fixed
natural_pdf / natural_text → paragraph

---

4. chunking.py
负责文本切块。

当前支持两类策略：

paragraph
适用于：
TXT
DOCX
自然语言结构较清晰的文档

特点：
段落优先切分
合并过短段落
对过长段落做定长切分
支持 overlap

page_fixed
适用于：
结构化 PDF
法律模板
政府文件
表格和编号较多的 PDF

特点：
按页优先保留上下文
页太长时在页内做固定长度切分
保留 page / chunk_index 等元数据

---

5. embeddings.py
负责调用嵌入模型，将文本转换为向量表示。

当前使用：
ZhipuAI embedding-3

---

6. vector_store.py
负责向量库管理。

当前能力包括：
初始化 ChromaDB collection
写入 chunk
按 source 删除文档
聚合并列出已导入文档

---

7. rag_pipeline.py
负责整个 RAG 流程的编排，是系统的核心调度层。

文档导入流程
文件 → parser → document_router → chunking → vector_store

问答流程
问题 → vector retrieval → context assembly → LLM generation

当前还会返回实际召回的 chunk，用于调试检索质量。

---

✨ 当前实现的能力

多格式接入
支持上传：
PDF
TXT
DOCX

---

文档管理
支持：
查看已导入文档
查看每个文档的页数和 chunk 数
删除指定文档索引

---

重复导入去重 / Re-index
同名文档重新导入时，会先删除旧索引，再重新写入新索引，避免重复召回和检索污染。

---

检索调试
查询后可以看到：

实际召回了哪些文本块
每个 chunk 来自哪一页
当前文档类型判断结果
使用了哪种 chunk 策略

这对排查 RAG 问题非常重要。

---

基础防幻觉
当前通过以下方式降低幻觉风险：

只基于召回上下文回答
若上下文不足，则明确返回“文档中未找到相关信息”
限制总 context 长度
显示引用来源

---

⚠️ 实践中的问题与优化

在实际测试过程中，发现不同文档不能统一使用同一种 chunk 策略。

尤其是在处理结构化 PDF（如法律合同模板、政府租赁模板、带大量编号/表格/占位符的文档）时，统一采用段落级切分会导致：

召回结果差
chunk 语义不完整
明显存在的关键词或条款难以命中
标题、条款编号、表格碎片被切成独立小块

问题的核心不是“PDF 一定不适合段落切”，而是：

对于被解析后的结构化模板文档，段落边界往往并不可靠，因此更适合按页优先切分，必要时再进行页内定长切分。

因此，当前版本开始引入“按文档类型选择切分策略”的思路：

结构化 PDF：page_fixed
自然语言文本：paragraph

这也是本项目从单纯 demo 向工程化 RAG 迈进的一步。

---

🛠️ 技术栈

Python
Streamlit
ChromaDB
ZhipuAI
pdfplumber
python-docx
python-dotenv

---

📦 安装与运行

1. 安装依赖

pip install -r requirements.txt

2. 配置环境变量

创建 `.env` 文件：

ZHIPUAI_API_KEY=your_api_key

3. 启动项目

streamlit run app.py

## 后续规划
- 替换为 OpenAI Embeddings + pgvector（生产环境）
- FastAPI 后端 + 前端界面
- Google Drive 自动同步
- hybird research

🧪 当前适合测试的文档类型

效果较好的文档：

FAQ 文档
普通 Word 文档
说明文档
结构较清晰的文本资料

需要特殊处理的文档：

法律合同模板
政府租赁模板
带大量编号、表格、占位符的 PDF
扫描件 PDF（当前未接 OCR）
📈 后续优化方向
增加 hybrid retrieval（语义检索 + 关键词检索）
增加 query rewrite（对短 query 做扩写）
增加相似度阈值过滤
增加 rerank
增强 PDF 清洗能力（页眉页脚、模板头去除）
支持 OCR（扫描件 / 图片）
增加 API 层（FastAPI）
增加评估与日志能力
## 界面预览

![合同智能查询系统](1.png)
![合同智能查询系统](2.png)
![合同智能查询系统](3.png)
