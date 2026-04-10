from typing import List
from langchain_core.documents import Document

from src.rag.vector_store import vector_store_manager


def retrieve_documents(query: str, k: int = 5) -> List[Document]:
    """检索相关文档"""
    return vector_store_manager.similarity_search(query, k=k)


def add_documents_to_store(documents: List[Document]):
    """添加文档到向量存储"""
    vector_store_manager.add_documents(documents)


def clear_vector_store():
    """清空向量存储"""
    vector_store_manager.delete_all_documents()