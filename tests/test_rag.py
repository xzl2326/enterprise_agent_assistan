"""
RAG模块测试

为什么怎么写：
1. 测试文档检索、向量存储管理、文档解析等核心RAG功能
2. 模拟向量数据库操作，避免外部依赖，实现可重复测试
3. 验证文档处理流程（解析、分块、嵌入、检索）的正确性

怎么写的作用是什么：
1. 确保知识库上传、检索、清空等操作正常工作
2. 验证文档解析器支持多种格式（PDF、TXT、DOCX等）
3. 为RAG系统扩展提供测试基础
"""

import pytest
from unittest.mock import patch, MagicMock
from langchain_core.documents import Document


def test_document_parser_structure():
    """测试文档解析器结构"""
    from src.rag.document_parser import DocumentParser
    
    parser = DocumentParser()
    
    # 验证解析器有必要的处理方法
    assert hasattr(parser, "process_file")
    assert hasattr(parser, "process_directory")
    
    # 验证支持的文件格式
    assert hasattr(parser, "supported_formats")
    assert isinstance(parser.supported_formats, list)
    assert len(parser.supported_formats) > 0


@patch("src.rag.document_parser.UnstructuredFileLoader")
@patch("src.rag.document_parser.RecursiveCharacterTextSplitter")
def test_process_file(mock_splitter, mock_loader):
    """测试处理单个文件"""
    from src.rag.document_parser import DocumentParser
    
    # 模拟文档加载和分割
    mock_doc = Document(page_content="测试文档内容")
    mock_loader.return_value.load.return_value = [mock_doc]
    
    mock_splitter_instance = MagicMock()
    mock_splitter_instance.split_documents.return_value = [
        Document(page_content="分块1"),
        Document(page_content="分块2")
    ]
    mock_splitter.return_value = mock_splitter_instance
    
    parser = DocumentParser()
    documents = parser.process_file("/path/to/test.pdf")
    
    assert isinstance(documents, list)
    assert len(documents) == 2
    assert all(isinstance(doc, Document) for doc in documents)
    
    # 验证加载器被调用
    mock_loader.assert_called_once_with("/path/to/test.pdf")
    mock_splitter.assert_called_once()
    mock_splitter_instance.split_documents.assert_called_once_with([mock_doc])


@patch("src.rag.document_parser.DocumentParser.process_file")
def test_process_directory(mock_process_file):
    """测试处理目录"""
    from src.rag.document_parser import DocumentParser
    
    # 模拟目录文件列表
    with patch("os.listdir") as mock_listdir, \
         patch("os.path.join") as mock_join, \
         patch("os.path.isfile") as mock_isfile:
        
        mock_listdir.return_value = ["doc1.pdf", "doc2.txt", "ignore.exe"]
        mock_isfile.return_value = True
        mock_join.side_effect = lambda *args: "/".join(args)
        
        # 模拟process_file返回文档
        mock_process_file.side_effect = [
            [Document(page_content="文档1")],
            [Document(page_content="文档2")]
        ]
        
        parser = DocumentParser()
        documents = parser.process_directory("/path/to/docs")
        
        assert isinstance(documents, list)
        assert len(documents) == 2
        
        # 验证只处理了支持的文件格式
        assert mock_process_file.call_count == 2
        mock_process_file.assert_any_call("/path/to/docs/doc1.pdf")
        mock_process_file.assert_any_call("/path/to/docs/doc2.txt")


@patch("src.rag.vector_store_manager")
def test_retrieve_documents(mock_vector_store):
    """测试文档检索"""
    from src.rag.retriever import retrieve_documents
    
    # 模拟检索结果
    mock_docs = [
        Document(page_content="相关内容1"),
        Document(page_content="相关内容2")
    ]
    mock_vector_store.similarity_search.return_value = mock_docs
    
    query = "测试查询"
    results = retrieve_documents(query, k=5)
    
    assert isinstance(results, list)
    assert len(results) == 2
    assert all(isinstance(doc, Document) for doc in results)
    
    # 验证向量存储被调用
    mock_vector_store.similarity_search.assert_called_once_with(query, k=5)


@patch("src.rag.vector_store_manager")
def test_add_documents_to_store(mock_vector_store):
    """测试添加文档到向量存储"""
    from src.rag.retriever import add_documents_to_store
    
    documents = [
        Document(page_content="文档1"),
        Document(page_content="文档2")
    ]
    
    add_documents_to_store(documents)
    
    # 验证向量存储被调用
    mock_vector_store.add_documents.assert_called_once_with(documents)


@patch("src.rag.vector_store_manager")
def test_clear_vector_store(mock_vector_store):
    """测试清空向量存储"""
    from src.rag.retriever import clear_vector_store
    
    clear_vector_store()
    
    # 验证向量存储被调用
    mock_vector_store.delete_all_documents.assert_called_once()


def test_vector_store_manager_structure():
    """测试向量存储管理器结构"""
    from src.rag.vector_store import VectorStoreManager
    
    manager = VectorStoreManager()
    
    # 验证管理器有必要的操作方法
    assert hasattr(manager, "similarity_search")
    assert hasattr(manager, "add_documents")
    assert hasattr(manager, "delete_all_documents")
    
    # 验证向量存储已初始化
    assert hasattr(manager, "vector_store")
    assert manager.vector_store is not None


@patch("src.rag.vector_store.Qdrant")
@patch("src.rag.vector_store.embeddings")
def test_vector_store_initialization(mock_embeddings, mock_qdrant):
    """测试向量存储初始化"""
    from src.rag.vector_store import VectorStoreManager
    
    # 模拟嵌入模型
    mock_embedding_model = MagicMock()
    mock_embeddings.return_value = mock_embedding_model
    
    # 模拟Qdrant客户端
    mock_qdrant_instance = MagicMock()
    mock_qdrant.return_value = mock_qdrant_instance
    
    manager = VectorStoreManager()
    
    # 验证嵌入模型被创建
    mock_embeddings.assert_called_once()
    
    # 验证Qdrant被初始化
    mock_qdrant.assert_called_once()
    
    # 验证向量存储已设置
    assert manager.vector_store == mock_qdrant_instance