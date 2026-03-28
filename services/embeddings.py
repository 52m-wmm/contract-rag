# 文本向量化
import os
from chromadb import Documents, EmbeddingFunction, Embeddings
from zhipuai import ZhipuAI
from dotenv import load_dotenv

load_dotenv()

ZHIPUAI_API_KEY = os.getenv("ZHIPUAI_API_KEY")
client_zhipu = ZhipuAI(api_key=ZHIPUAI_API_KEY)


class ZhipuEmbeddingFunction(EmbeddingFunction):
    def __call__(self, input: Documents) -> Embeddings:
        embeddings = []
        for text in input:
            response = client_zhipu.embeddings.create(model="embedding-3", input=text)
            embeddings.append(response.data[0].embedding)
        return embeddings
