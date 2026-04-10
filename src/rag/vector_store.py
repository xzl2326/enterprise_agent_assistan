import os
from typing import List, Optional
from langchain_qdrant import QdrantVectorStore
from langchain_core.documents import Document
from qdrant_client import QdrantClient
from qdrant_client.http import models
from langchain_community.embeddings import DashScopeEmbeddings
from src.config.settings import settings

class VectorStoreManager:
    def __init__(self):
        # ===== 阿里云模型，直接加载，无 HF =====
        self.embedding = None
        self.embedding_model =settings.embedding_model
        self.embedding_dimension = settings.embedding_dimension

        # ===== 下面 Qdrant 代码不变 =====
        self.qdrant_available = False
        self.client = None
        self.collection_name = settings.qdrant_collection_name

        try:
            self.client = QdrantClient(url=settings.qdrant_url, timeout=10)
            self.client.get_collections()
            self.qdrant_available = True
            self._ensure_collection_exists()
        except Exception as e:
            print(f"[WARN] Qdrant连接失败: {e}")

    # ... 剩下代码全部保持不变 ...

    def _ensure_collection_exists(self):
        """确保向量集合存在"""
        if not self.qdrant_available or not self.client:
            return

        try:
            collections = self.client.get_collections().collections
            collection_names = [col.name for col in collections]

            if self.collection_name not in collection_names:
                self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=models.VectorParams(
                        size=self.embedding_dimension,  # 嵌入模型维度
                        distance=models.Distance.COSINE
                    )
                )
                print(f"[INFO] 创建集合: {self.collection_name}")
        except Exception as e:
            print(f"[WARN] 确保集合存在失败: {e}")

    def get_vector_store(self) -> Optional[QdrantVectorStore]:
        """获取向量存储实例"""
        if not self.qdrant_available or not self.client:
            print("[WARN] Qdrant不可用，无法获取向量存储")
            return None

        # 懒加载嵌入模型
        if self.embedding is None:
            self.embedding = DashScopeEmbeddings(
                model=self.embedding_model,  # 你的配置里的阿里云模型名
                dashscope_api_key=settings.dashscope_api_key  # 阿里云API密钥
            )

        return QdrantVectorStore(
            client=self.client,
            collection_name=self.collection_name,
            embedding=self.embedding,
        )

    def add_documents(self, documents: List[Document]):
        """添加文档到向量库"""
        vector_store = self.get_vector_store()
        if vector_store is None:
            print("[WARN] 向量存储不可用，无法添加文档")
            return

        try:
            vector_store.add_documents(documents)
            print(f"[INFO] 成功添加 {len(documents)} 个文档到向量库")
        except Exception as e:
            print(f"[ERROR] 添加文档失败: {e}")

    def similarity_search(self, query: str, k: int = 5) -> List[Document]:
        """相似性搜索"""
        vector_store = self.get_vector_store()
        if vector_store is None:
            print("[WARN] 向量存储不可用，返回空结果")
            return []

        try:
            return vector_store.similarity_search(query, k=k)
        except Exception as e:
            print(f"[ERROR] 相似性搜索失败: {e}")
            return []

    def delete_all_documents(self):
        """删除所有文档"""
        if not self.qdrant_available or not self.client:
            print("[WARN] Qdrant不可用，无法删除文档")
            return

        try:
            self.client.delete_collection(self.collection_name)
            print("[INFO] 已删除集合")
            self._ensure_collection_exists()
        except Exception as e:
            print(f"[ERROR] 删除文档失败: {e}")


# 全局向量存储管理器实例
vector_store_manager = VectorStoreManager()