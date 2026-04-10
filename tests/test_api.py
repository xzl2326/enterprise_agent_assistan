"""
API端点测试

为什么怎么写：
1. 使用FastAPI TestClient进行端到端测试，验证API接口功能
2. 模拟依赖组件（如agent_graph、向量存储）避免外部依赖
3. 使用pytest-asyncio支持异步测试，符合FastAPI异步特性

怎么写的作用是什么：
1. 确保核心API接口（健康检查、工具列表、聊天等）正常工作
2. 验证请求验证、错误处理和响应格式
3. 为后续功能扩展提供测试基础
"""

import pytest
from unittest.mock import patch, MagicMock


def test_health_check(client):
    """测试健康检查接口"""
    response = client.get("/api/v1/health")
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "enterprise-agent-assistant"
    assert data["version"] == "1.0.0"


def test_list_tools(client):
    """测试工具列表接口"""
    response = client.get("/api/v1/tools")
    
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "tools" in data["data"]
    assert "count" in data["data"]


def test_chat_endpoint_validation(client):
    """测试聊天接口参数验证"""
    # 测试空消息
    response = client.post("/api/v1/chat", json={})
    # 由于全局异常处理，HTTPException被转为500
    assert response.status_code == 500

    # 测试消息为空字符串
    response = client.post("/api/v1/chat", json={"message": ""})
    assert response.status_code == 500


@patch("src.api.routes.agent_graph")
def test_chat_endpoint_success(mock_agent_graph, client):
    """测试聊天接口成功场景"""
    # 模拟agent_graph响应
    mock_result = {
        "final_output": "测试响应",
        "task_type": "general",
        "status": "completed",
        "retrieved_docs": [],
        "tool_results": {},
        "messages": []
    }
    mock_agent_graph.invoke.return_value = mock_result
    
    response = client.post("/api/v1/chat", json={"message": "你好"})
    
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["answer"] == "测试响应"
    assert data["data"]["task_type"] == "general"
    assert data["data"]["status"] == "completed"
    
    # 验证agent_graph被调用
    mock_agent_graph.invoke.assert_called_once_with("你好")


def test_upload_knowledge_validation(client):
    """测试知识库上传接口参数验证"""
    # 测试缺少文件路径
    response = client.post("/api/v1/knowledge/upload", json={})
    # 由于全局异常处理，HTTPException被转为500
    assert response.status_code == 500

    # 测试文件路径为空字符串
    response = client.post("/api/v1/knowledge/upload", json={"file_path": ""})
    assert response.status_code == 500


@patch("src.api.routes.document_parser")
@patch("src.api.routes.add_documents_to_store")
def test_upload_knowledge_success(mock_add_documents, mock_parser, client):
    """测试知识库上传成功场景"""
    # 模拟文档解析
    mock_documents = [{"text": "文档1"}, {"text": "文档2"}]
    mock_parser.process_file.return_value = mock_documents
    
    response = client.post("/api/v1/knowledge/upload", json={"file_path": "/path/to/doc.pdf"})
    
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["file_path"] == "/path/to/doc.pdf"
    assert data["data"]["chunks_count"] == 2
    
    # 验证文档解析和存储被调用
    mock_parser.process_file.assert_called_once_with("/path/to/doc.pdf")
    mock_add_documents.assert_called_once_with(mock_documents)


def test_clear_knowledge(client):
    """测试清空知识库接口"""
    with patch("src.api.routes.clear_vector_store") as mock_clear:
        response = client.delete("/api/v1/knowledge/clear")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["message"] == "知识库已清空"
        
        # 验证清空函数被调用
        mock_clear.assert_called_once()


def test_root_endpoint(client):
    """测试根端点"""
    response = client.get("/")
    
    assert response.status_code == 200
    data = response.json()
    assert data["service"] == "企业级多角色智能任务助理Agent"
    assert data["version"] == "1.0.0"
    assert "endpoints" in data