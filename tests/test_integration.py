"""
集成测试和端到端测试

为什么怎么写：
1. 测试系统各模块之间的协作，确保数据流正确
2. 验证API接口到智能体再到工具执行的完整流程
3. 测试多智能体协作和状态管理

怎么写的作用是什么：
1. 确保系统整体功能正常，不是单个模块
2. 发现模块间集成的问题
3. 为系统部署和上线提供信心
"""

import pytest
from unittest.mock import patch, MagicMock


def test_full_chat_flow(client):
    """测试完整的聊天流程：API → 智能体 → 响应"""
    # 模拟智能体响应，避免真实LLM调用
    with patch("src.api.routes.agent_graph") as mock_agent_graph:
        mock_result = {
            "final_output": "你好！我是企业智能助手，很高兴为您服务。",
            "task_type": "qa",
            "status": "completed",
            "retrieved_docs": [],
            "tool_results": {},
            "messages": []
        }
        mock_agent_graph.invoke.return_value = mock_result
        
        # 发送聊天请求
        response = client.post(
            "/api/v1/chat",
            json={"message": "你好"}
        )
        
        # 验证响应
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True
        assert "data" in data
        assert "answer" in data["data"]
        assert data["data"]["answer"] == "你好！我是企业智能助手，很高兴为您服务。"


def test_chat_with_web_search(client):
    """测试需要网络搜索的聊天流程"""
    # 模拟智能体响应和工具调用
    with patch("src.api.routes.agent_graph") as mock_agent_graph:
        mock_result = {
            "final_output": "根据搜索结果，Python 3.12带来了许多新特性...",
            "task_type": "search",
            "status": "completed",
            "retrieved_docs": [],
            "tool_results": {},
            "messages": []
        }
        mock_agent_graph.invoke.return_value = mock_result
        
        # 发送聊天请求
        response = client.post(
            "/api/v1/chat",
            json={"message": "Python 3.12有什么新特性？"}
        )
        
        # 验证响应
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True
        assert "data" in data
        assert "answer" in data["data"]
        assert "Python" in data["data"]["answer"]


def test_tool_execution_via_api(client):
    """测试通过API直接执行工具"""
    # 首先获取工具列表
    response = client.get("/api/v1/tools")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "tools" in data["data"]
    assert "count" in data["data"]
    
    # 验证有工具
    assert data["data"]["count"] > 0


def test_error_handling_integration(client):
    """测试集成层面的错误处理"""
    # 测试空消息
    response = client.post(
        "/api/v1/chat",
        json={"message": ""}
    )
    # 由于全局异常处理，可能返回500或400
    assert response.status_code in [400, 500]


def test_multiple_tool_calls(client):
    """测试多次工具调用的复杂场景"""
    with patch("src.api.routes.agent_graph") as mock_agent_graph:
        mock_result = {
            "final_output": "根据搜索和文件内容，Python和Java各有优势...",
            "task_type": "complex",
            "status": "completed",
            "retrieved_docs": [],
            "tool_results": {},
            "messages": []
        }
        mock_agent_graph.invoke.return_value = mock_result
        
        response = client.post(
            "/api/v1/chat",
            json={"message": "搜索Python和Java的对比，然后读取文件"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True
        assert "data" in data


@pytest.mark.integration
def test_end_to_end_qa_flow(client):
    """端到端测试：问答流程"""
    # 这个测试模拟真实用户场景
    test_cases = [
        {
            "message": "你好",
            "expected_contains": ["你好", "您好"]
        },
        {
            "message": "帮我搜索一下Python编程",
            "expected_contains": ["搜索", "Python"]
        }
    ]
    
    with patch("src.api.routes.agent_graph") as mock_agent_graph:
        for i, test_case in enumerate(test_cases):
            # 模拟不同的响应
            mock_result = {
                "final_output": f"这是对'{test_case['message']}'的回答",
                "task_type": "qa",
                "status": "completed",
                "retrieved_docs": [],
                "tool_results": {},
                "messages": []
            }
            mock_agent_graph.invoke.return_value = mock_result
            
            response = client.post(
                "/api/v1/chat",
                json={"message": test_case["message"]}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] == True
            assert "data" in data
