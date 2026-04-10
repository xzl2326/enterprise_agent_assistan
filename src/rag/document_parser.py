import os
from typing import List
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import (
    TextLoader,
    PyPDFLoader,
    UnstructuredWordDocumentLoader,
    UnstructuredExcelLoader,
    UnstructuredPowerPointLoader
)

from src.config.settings import settings


def load_document(file_path: str) -> List[Document]:
    """加载文档"""
    file_ext = os.path.splitext(file_path)[1].lower()

    try:
        if file_ext == ".txt":
            loader = TextLoader(file_path, encoding="utf-8")
        elif file_ext == ".pdf":
            loader = PyPDFLoader(file_path)
        elif file_ext in [".docx", ".doc"]:
            loader = UnstructuredWordDocumentLoader(file_path)
        elif file_ext in [".xlsx", ".xls", ".csv"]:
            loader = UnstructuredExcelLoader(file_path)
        elif file_ext in [".pptx", ".ppt"]:
            loader = UnstructuredPowerPointLoader(file_path)
        else:
            # 默认按文本处理
            loader = TextLoader(file_path, encoding="utf-8")

        return loader.load()
    except Exception as e:
        raise Exception(f"文档加载失败: {str(e)}")


class DocumentParser:
    """文档解析器，支持多种格式"""

    def __init__(self):
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=settings.chunk_size,
            chunk_overlap=settings.chunk_overlap,
            separators=["\n\n", "\n", "。", "！", "？", ".", "!", "?", " ", ""]
        )

    def split_documents(self, documents: List[Document]) -> List[Document]:
        """分割文档为小块"""
        return self.text_splitter.split_documents(documents)

    def process_file(self, file_path: str) -> List[Document]:
        """处理单个文件：加载并分割"""
        documents = load_document(file_path)
        return self.split_documents(documents)

    def process_directory(self, directory_path: str) -> List[Document]:
        """处理整个目录下的文档"""
        all_documents = []

        for root, dirs, files in os.walk(directory_path):
            for file in files:
                file_path = os.path.join(root, file)
                try:
                    docs = self.process_file(file_path)
                    all_documents.extend(docs)
                    print(f"成功处理: {file_path} ({len(docs)}个块)")
                except Exception as e:
                    print(f"处理失败 {file_path}: {str(e)}")

        return all_documents


# 全局文档解析器实例
document_parser = DocumentParser()