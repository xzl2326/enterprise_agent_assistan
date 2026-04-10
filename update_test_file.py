import pathlib
from pathlib import Path

# 创建完整的测试文件内容
content = '''"""
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
'''

# 写入文件
file_path = Path('tests/test_integration.py')
file_path.write_text(content, encoding='utf-8')
print('File updated:', file_path.exists())
print('File content:', file_path.read_text(encoding='utf-8')[:500] if file_path.exists() else 'N/A')