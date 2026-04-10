from typing import Dict, Any, List
import litellm
import json

from src.agents.state import AgentState
from src.config.settings import settings
from src.tools.web_search import web_search, search_and_summarize
from src.tools.file_tool import read_file, write_file, list_files, analyze_file
from src.tools.api_tool import call_api, get_weather, get_exchange_rate
from src.utils.logger import log_agent_action


class ToolExecutionAgent:
    """工具执行Agent：函数调用、联网搜索、自动化任务处理"""

    def __init__(self):
        self.model = settings.litellm_model
        self.available_tools = {
            "web_search": {
                "function": web_search,
                "description": "使用DuckDuckGo进行网页搜索",
                "parameters": {"query": "搜索关键词", "max_results": "最大结果数（默认5）"}
            },
            "search_and_summarize": {
                "function": search_and_summarize,
                "description": "搜索并总结搜索结果",
                "parameters": {"query": "搜索关键词", "max_results": "最大结果数（默认3）"}
            },
            "read_file": {
                "function": read_file,
                "description": "读取文件内容",
                "parameters": {"file_path": "文件路径"}
            },
            "write_file": {
                "function": write_file,
                "description": "写入文件",
                "parameters": {"file_path": "文件路径", "content": "要写入的内容"}
            },
            "list_files": {
                "function": list_files,
                "description": "列出目录中的文件",
                "parameters": {"directory": "目录路径", "extension": "文件扩展名过滤（可选）"}
            },
            "analyze_file": {
                "function": analyze_file,
                "description": "分析文件信息",
                "parameters": {"file_path": "文件路径"}
            },
            "call_api": {
                "function": call_api,
                "description": "调用API接口",
                "parameters": {
                    "url": "API地址",
                    "method": "HTTP方法（默认GET）",
                    "headers": "请求头（可选）",
                    "params": "URL参数（可选）",
                    "json_data": "JSON数据（可选）"
                }
            },
            "get_weather": {
                "function": get_weather,
                "description": "获取天气信息",
                "parameters": {"city": "城市名称"}
            },
            "get_exchange_rate": {
                "function": get_exchange_rate,
                "description": "获取汇率信息",
                "parameters": {"base_currency": "基础货币", "target_currency": "目标货币"}
            }
        }

    def _select_tools(self, task_description: str) -> List[str]:
        """根据任务描述选择合适工具"""
        prompt = f"""
        根据以下任务描述，选择最合适的工具（从可用工具列表中选择）：
        
        任务描述：{task_description}
        
        可用工具：
        {json.dumps(list(self.available_tools.keys()), indent=2)}
        
        每个工具的描述：
        {json.dumps({k: v['description'] for k, v in self.available_tools.items()}, indent=2)}
        
        请以JSON数组格式返回选择的工具名称，例如：["web_search", "call_api"]
        如果不需要工具，返回空数组 []。
        """

        response = litellm.completion(
            model=self.model,
            messages=[
                {"role": "system", "content": "你是一个工具选择专家"},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1
        )

        try:
            selected_tools = json.loads(response.choices[0].message.content)
            return selected_tools if isinstance(selected_tools, list) else []
        except:
            return []

    def _extract_parameters(self, task_description: str, tool_name: str) -> Dict[str, Any]:
        """从任务描述中提取工具参数"""
        tool_info = self.available_tools.get(tool_name)
        if not tool_info:
            return {}

        prompt = f"""
        任务描述：{task_description}
        
        需要使用的工具：{tool_name}
        工具描述：{tool_info['description']}
        工具参数：{json.dumps(tool_info['parameters'], indent=2)}
        
        请从任务描述中提取工具参数，并以JSON格式返回。
        示例：对于web_search工具，如果任务描述是"搜索北京的天气"，则返回{{"query": "北京天气"}}
        """

        response = litellm.completion(
            model=self.model,
            messages=[
                {"role": "system", "content": "你是一个参数提取专家"},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1
        )

        try:
            params = json.loads(response.choices[0].message.content)
            return params if isinstance(params, dict) else {}
        except:
            return {}

    def execute_tool(self, tool_name: str, params: Dict[str, Any]) -> Any:
        """执行工具"""
        tool_info = self.available_tools.get(tool_name)
        if not tool_info:
            return f"工具不存在: {tool_name}"

        try:
            log_agent_action("ToolAgent", f"执行工具: {tool_name}", {"params": params})
            result = tool_info["function"](**params)
            return result
        except Exception as e:
            error_msg = f"工具执行失败: {str(e)}"
            log_agent_action("ToolAgent", f"工具执行失败: {tool_name}", {"error": str(e)})
            return error_msg

    def process(self, state: AgentState) -> AgentState:
        """处理工具执行任务"""
        subtasks = state.get("subtasks", [])
        tool_results = {}

        for i, subtask in enumerate(subtasks):
            task_type = subtask.get("type", "")
            task_desc = subtask.get("description", "")

            # 只处理工具类任务
            if task_type in ["search", "tool", "api", "file"]:
                # 选择工具
                selected_tools = self._select_tools(task_desc)

                for tool_name in selected_tools:
                    # 提取参数
                    params = self._extract_parameters(task_desc, tool_name)

                    # 执行工具
                    result = self.execute_tool(tool_name, params)

                    # 存储结果
                    tool_key = f"{tool_name}_{i}"
                    tool_results[tool_key] = {
                        "tool": tool_name,
                        "params": params,
                        "result": result,
                        "task": task_desc
                    }

        # 更新状态
        state["tool_results"].update(tool_results)

        # 添加消息
        if tool_results:
            state["messages"].append({
                "role": "assistant",
                "content": f"工具执行完成，执行了 {len(tool_results)} 个工具"
            })

        return state


def tool_node(state: AgentState) -> AgentState:
    """工具节点函数，用于LangGraph"""
    agent = ToolExecutionAgent()
    return agent.process(state)