import requests
import json
from typing import Dict, Any, Optional
from datetime import datetime


def call_api(
    url: str,
    method: str = "GET",
    headers: Optional[Dict[str, str]] = None,
    params: Optional[Dict[str, Any]] = None,
    data: Optional[Dict[str, Any]] = None,
    json_data: Optional[Dict[str, Any]] = None,
    timeout: int = 30
) -> Dict[str, Any]:
    """
    调用API接口

    Args:
        url: API地址
        method: HTTP方法（GET, POST, PUT, DELETE等）
        headers: 请求头
        params: URL参数
        data: 表单数据
        json_data: JSON数据
        timeout: 超时时间（秒）

    Returns:
        响应结果字典
    """
    try:
        # 默认请求头
        if headers is None:
            headers = {
                "Content-Type": "application/json",
                "User-Agent": "Enterprise-Agent/1.0"
            }

        response = requests.request(
            method=method.upper(),
            url=url,
            headers=headers,
            params=params,
            data=data,
            json=json_data,
            timeout=timeout
        )

        # 尝试解析JSON响应
        try:
            response_data = response.json()
        except json.JSONDecodeError:
            response_data = response.text

        return {
            "status_code": response.status_code,
            "success": 200 <= response.status_code < 300,
            "data": response_data,
            "headers": dict(response.headers),
            "elapsed": response.elapsed.total_seconds()
        }
    except requests.exceptions.Timeout:
        return {
            "status_code": 408,
            "success": False,
            "data": "请求超时",
            "error": "timeout"
        }
    except Exception as e:
        return {
            "status_code": 500,
            "success": False,
            "data": f"请求失败: {str(e)}",
            "error": str(e)
        }


def get_weather(city: str) -> Dict[str, Any]:
    """
    获取天气信息（示例API）
    """
    # 这里使用一个公开的天气API示例
    # 实际使用时需要替换为真实的API
    return {
        "city": city,
        "temperature": "25°C",
        "condition": "晴天",
        "humidity": "65%",
        "wind_speed": "10 km/h",
        "forecast": "未来三天天气晴朗",
        "source": "模拟数据",
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }


def get_exchange_rate(base_currency: str, target_currency: str) -> Dict[str, Any]:
    """
    获取汇率信息（示例API）
    """
    # 模拟汇率数据
    rates = {
        "USD": {"CNY": 7.2, "EUR": 0.92, "JPY": 150},
        "CNY": {"USD": 0.14, "EUR": 0.13, "JPY": 21},
        "EUR": {"USD": 1.09, "CNY": 7.8, "JPY": 163},
        "JPY": {"USD": 0.0067, "CNY": 0.048, "EUR": 0.0061}
    }

    if base_currency in rates and target_currency in rates[base_currency]:
        rate = rates[base_currency][target_currency]
        return {
            "base": base_currency,
            "target": target_currency,
            "rate": rate,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
    else:
        return {
            "error": f"不支持{base_currency}到{target_currency}的汇率查询",
            "available_pairs": ["USD-CNY", "USD-EUR", "USD-JPY", "CNY-USD", "CNY-EUR", "CNY-JPY"]
        }