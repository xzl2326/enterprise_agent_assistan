from duckduckgo_search import DDGS
from typing import Dict, List, Any
import json


def web_search(query: str, max_results: int = 5) -> List[Dict[str, str]]:
    """
    使用DuckDuckGo进行网页搜索

    Args:
        query: 搜索查询
        max_results: 最大结果数量

    Returns:
        搜索结果列表，每个结果包含title、link、snippet
    """
    try:
        with DDGS() as ddgs:
            results = []
            for result in ddgs.text(query, max_results=max_results):
                results.append({
                    "title": result.get("title", ""),
                    "link": result.get("href", ""),
                    "snippet": result.get("body", "")
                })
            return results
    except Exception as e:
        return [{
            "title": "搜索失败",
            "link": "",
            "snippet": f"搜索时发生错误: {str(e)}"
        }]


def search_and_summarize(query: str, max_results: int = 3) -> str:
    """
    搜索并总结搜索结果
    """
    results = web_search(query, max_results)

    if not results or "搜索失败" in results[0]["title"]:
        return "无法获取搜索信息。"

    summary = "搜索结果:\n"
    for i, result in enumerate(results, 1):
        summary += f"{i}. {result['title']}\n"
        summary += f"   摘要: {result['snippet'][:150]}...\n"
        summary += f"   链接: {result['link']}\n\n"

    return summary