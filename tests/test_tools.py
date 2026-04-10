"""
工具模块测试

为什么怎么写：
1. 测试各类工具（网页搜索、文件操作、API调用）的功能和参数验证
2. 模拟外部依赖（如网络请求、文件系统），实现可重复的单元测试
3. 验证工具集成和错误处理机制

怎么写的作用是什么：
1. 确保工具函数按预期工作，参数验证有效
2. 验证工具在智能体系统中的集成方式
3. 为工具扩展和新工具开发提供测试基础
"""

import pytest
from unittest.mock import patch, MagicMock
import os
import json


def test_web_search_tool():
    """测试网页搜索工具"""
    from src.tools.web_search import web_search
    
    with patch("src.tools.web_search.DDGS") as mock_ddgs:
        # 模拟搜索结果
        mock_results = [
            {"title": "结果1", "body": "内容1", "href": "http://example.com/1"},
            {"title": "结果2", "body": "内容2", "href": "http://example.com/2"}
        ]
        mock_ddgs.return_value.__enter__.return_value.text.return_value = mock_results
        
        query = "测试查询"
        max_results = 3
        results = web_search(query, max_results)
        
        # 验证结果格式
        assert isinstance(results, list)
        assert len(results) <= max_results
        
        # 验证DDGS被调用
        mock_ddgs.return_value.__enter__.return_value.text.assert_called_once_with(
            query, max_results=max_results
        )


def test_search_and_summarize():
    """测试搜索并总结工具"""
    from src.tools.web_search import search_and_summarize
    
    with patch("src.tools.web_search.web_search") as mock_web_search:

        # 模拟搜索结果
        mock_web_search.return_value = [
            {"title": "结果1", "link": "http://example.com/1", "snippet": "这是第一个结果的摘要内容，比较长一些"},
            {"title": "结果2", "link": "http://example.com/2", "snippet": "这是第二个结果的摘要内容"}
        ]
        
        query = "测试查询"
        result = search_and_summarize(query,3)
        
        # 验证结果包含搜索结果
        assert "搜索结果" in result
        assert "结果1" in result
        assert "结果2" in result
        assert "http://example.com/1" in result
        assert "http://example.com/2" in result

        # 验证web_search被调用
        mock_web_search.assert_called_once_with(query, 3)


@patch("builtins.open")
def test_read_file_tool(mock_open):
    """测试读取文件工具"""
    from src.tools.file_tool import read_file
    
    # 模拟文件内容
    mock_file = MagicMock()
    mock_file.read.return_value = "文件内容"
    mock_open.return_value.__enter__.return_value = mock_file
    
    file_path = "/path/to/file.txt"
    result = read_file(file_path)
    
    assert result == "文件内容"
    mock_open.assert_called_once_with(file_path, "r", encoding="utf-8")


@patch("builtins.open")
def test_write_file_tool(mock_open):
    """测试写入文件工具"""
    from src.tools.file_tool import write_file
    
    mock_file = MagicMock()
    mock_open.return_value.__enter__.return_value = mock_file
    
    file_path = "/path/to/file.txt"
    content = "要写入的内容"
    
    result = write_file(file_path, content)
    
    assert result == f"文件已成功写入: {file_path}"
    mock_open.assert_called_once_with(file_path, "w", encoding="utf-8")
    mock_file.write.assert_called_once_with(content)


@patch("os.path.isfile")
@patch("os.path.join")
@patch("os.path.exists")
@patch("os.listdir")
def test_list_files_tool(mock_listdir, mock_exists, mock_join, mock_isfile):
    """测试列出文件工具"""
    from src.tools.file_tool import list_files
    
    # 模拟目录存在
    mock_exists.return_value = True
    mock_join.side_effect = lambda a, b: f"{a}/{b}"
    mock_isfile.side_effect = lambda path: not path.endswith("subdir")

    # 模拟目录内容
    mock_listdir.return_value = ["file1.txt", "file2.pdf", "subdir"]
    
    directory = "/path/to/dir"
    result = list_files(directory)
    
    assert isinstance(result, list)
    assert len(result) == 2  # 只返回文件，不返回目录
    assert "/path/to/dir/file1.txt" in result
    assert "/path/to/dir/file2.pdf" in result

    mock_exists.assert_called_once_with(directory)
    mock_listdir.assert_called_once_with(directory)


@patch("os.path.splitext")
@patch("os.stat")
@patch("os.path.isfile")
@patch("os.path.exists")
def test_analyze_file_tool(mock_exists, mock_isfile, mock_stat, mock_splitext):
    """测试分析文件工具"""
    from src.tools.file_tool import analyze_file

    # 模拟文件信息
    mock_exists.return_value = True
    mock_isfile.return_value = True

    # 模拟os.stat返回
    mock_stat_result = type('StatResult', (), {
        'st_size': 1024,  # 1KB
        'st_ctime': 1609459200,  # 创建时间戳
        'st_mtime': 1609545600,  # 修改时间戳
    })()
    mock_stat.return_value = mock_stat_result

    mock_splitext.return_value = ("/path/to/file", ".txt")

    file_path = "/path/to/file.txt"
    result = analyze_file(file_path)

    assert isinstance(result, dict)
    # 检查是否返回了有效结果或错误信息
    assert "path" in result or "error" in result

    if "path" in result:
        assert result["path"] == file_path
        assert result["size_bytes"] == 1024
        assert "size_human" in result
        assert "created" in result
        assert "modified" in result
        assert result["extension"] == ".txt"
        assert result["exists"] == True

    mock_exists.assert_called_once_with(file_path)
    mock_stat.assert_called_once_with(file_path)


@patch("requests.request")
def test_call_api_tool(mock_request):
    """测试调用API工具"""
    from src.tools.api_tool import call_api
    
    # 模拟API响应
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"key": "value"}
    mock_request.return_value = mock_response
    
    url = "https://api.example.com/data"
    method = "GET"
    headers = {"Authorization": "Bearer token"}
    params = {"page": 1}
    
    result = call_api(url, method, headers, params)
    
    assert isinstance(result, dict)
    assert result["status_code"] == 200
    assert result["data"] == {"key": "value"}
    
    # 验证requests被调用
    mock_request.assert_called_once_with(
        method=method,
        url=url,
        headers=headers,
        params=params,
        data=None,
        json=None,
        timeout=30
    )


def test_get_weather_tool():
    """测试获取天气工具"""
    from src.tools.api_tool import get_weather
    
    city = "北京"
    result = get_weather(city)
    
    assert isinstance(result, dict)
    assert result["city"] == city
    assert "temperature" in result
    assert "condition" in result
    assert "humidity" in result
    assert "wind_speed" in result
    assert "forecast" in result
    assert "source" in result
    assert "timestamp" in result


def test_get_exchange_rate_tool():
    """测试获取汇率工具"""
    from src.tools.api_tool import get_exchange_rate
    
    base_currency = "USD"
    target_currency = "CNY"
    result = get_exchange_rate(base_currency, target_currency)
    
    assert isinstance(result, dict)
    assert result["base"] == base_currency
    assert result["target"] == target_currency
    assert "rate" in result
    assert "timestamp" in result


def test_tool_error_handling():
    """测试工具错误处理"""
    from src.tools.file_tool import read_file
    
    with patch("builtins.open", side_effect=FileNotFoundError("文件不存在")):
        file_path = "/nonexistent/file.txt"
        result = read_file(file_path)
        
        assert "读取文件失败" in result
        assert "文件不存在" in result


def test_tool_parameter_validation():
    """测试工具参数验证"""
    from src.tools.web_search import web_search
    
    # 测试边界参数 - 函数应该能处理而不崩溃
    with patch("src.tools.web_search.DDGS") as mock_ddgs:
        # 模拟搜索结果为空
        mock_ddgs.return_value.__enter__.return_value.text.return_value = []

        # 测试空查询
        result = web_search("", max_results=1)
        assert isinstance(result, list)

        # 测试max_results为0
        result = web_search("测试", max_results=0)
        assert isinstance(result, list)

        # 测试有效参数
        result = web_search("测试", max_results=1)
        assert isinstance(result, list)
