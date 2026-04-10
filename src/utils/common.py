import json
import re
from typing import Any, Dict, List, Optional
from datetime import datetime


def safe_json_parse(json_str: str) -> Optional[Dict[str, Any]]:
    """安全解析JSON字符串"""
    try:
        return json.loads(json_str)
    except json.JSONDecodeError:
        # 尝试修复常见的JSON格式问题
        try:
            # 处理单引号
            json_str = json_str.replace("'", '"')
            # 处理未转义的双引号
            json_str = re.sub(r'(?<!\\)"', '\\"', json_str)
            return json.loads(json_str)
        except:
            return None


def format_datetime(dt: datetime = None) -> str:
    """格式化日期时间"""
    if dt is None:
        dt = datetime.now()
    return dt.strftime("%Y-%m-%d %H:%M:%S")


def truncate_text(text: str, max_length: int = 200) -> str:
    """截断文本"""
    if len(text) <= max_length:
        return text
    return text[:max_length] + "..."


def extract_tool_calls(text: str) -> List[Dict[str, str]]:
    """从文本中提取工具调用指令"""
    # 简单的工具调用提取逻辑
    # 实际项目中可以使用更复杂的解析
    tool_calls = []

    # 匹配类似 [TOOL: search, query="天气"] 的格式
    pattern = r'\[TOOL:\s*([^,]+),\s*([^\]]+)\]'
    matches = re.findall(pattern, text, re.IGNORECASE)

    for match in matches:
        tool_name = match[0].strip()
        params_str = match[1].strip()

        # 简单解析参数
        params = {}
        param_pairs = re.findall(r'(\w+)="([^"]*)"', params_str)
        for key, value in param_pairs:
            params[key] = value

        tool_calls.append({
            "tool": tool_name,
            "params": params
        })

    return tool_calls


def validate_email(email: str) -> bool:
    """验证邮箱格式"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))