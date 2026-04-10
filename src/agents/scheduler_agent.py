from typing import Dict, Any
import litellm
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import StateGraph, END

from src.agents.state import AgentState
from src.config.settings import settings


class SchedulerAgent:
    """调度Agent：任务接收、拆解、分配"""

    def __init__(self):
        self.model = settings.litellm_model

    def _classify_task(self, user_input: str) -> str:
        """分类任务类型"""
        prompt = f"""
        请分析以下用户请求，判断任务类型：
        1. "qa" - 纯知识问答类，只需要从知识库中查找信息
        2. "tool" - 纯工具执行类，需要调用工具（如搜索、计算、API调用等）
        3. "mixed" - 混合类，既需要知识库信息也需要工具执行
        
        用户请求：{user_input}
        
        只需返回任务类型（qa/tool/mixed），不要额外解释。
        """

        # 准备litellm参数
        litellm_kwargs = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": "你是一个任务分类助手"},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.1
        }

        # 如果配置了api_base，则添加到参数中
        if settings.litellm_api_base:
            litellm_kwargs["api_base"] = settings.litellm_api_base

        response = litellm.completion(**litellm_kwargs)

        task_type = response.choices[0].message.content.strip().lower()
        return task_type if task_type in ["qa", "tool", "mixed"] else "mixed"

    def _decompose_task(self, user_input: str, task_type: str) -> list:
        """拆解任务为子任务"""
        if task_type == "qa":
            return [{"type": "rag", "description": f"回答: {user_input}"}]
        elif task_type == "tool":
            prompt = f"""
            用户请求：{user_input}
            
            请将上述任务拆解为具体的工具调用步骤。每个步骤应包含：
            1. 工具类型（search/file/api/calculator等）
            2. 具体操作描述
            3. 预期输出
            
            以JSON格式返回，格式示例：
            [
                {{"type": "search", "description": "搜索最新信息", "tool": "web_search"}},
                {{"type": "calculate", "description": "计算结果", "tool": "calculator"}}
            ]
            """
        else:  # mixed
            prompt = f"""
            用户请求：{user_input}
            
            这是一个混合任务，请拆解为以下步骤：
            1. 需要从知识库检索的信息
            2. 需要调用的工具
            3. 需要综合分析的内容
            
            以JSON格式返回，格式示例：
            [
                {{"type": "rag", "description": "从知识库查找相关信息"}},
                {{"type": "search", "description": "搜索最新动态", "tool": "web_search"}},
                {{"type": "analysis", "description": "综合分析结果"}}
            ]
            """

        # 准备litellm参数
        litellm_kwargs = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": "你是一个任务拆解专家"},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.1
        }

        # 如果配置了api_base，则添加到参数中
        if settings.litellm_api_base:
            litellm_kwargs["api_base"] = settings.litellm_api_base

        response = litellm.completion(**litellm_kwargs)

        # 这里需要解析JSON，简化处理直接返回
        import json
        try:
            return json.loads(response.choices[0].message.content)
        except:
            # 如果解析失败，返回默认结构
            return [{"type": task_type, "description": user_input}]

    def process(self, state: AgentState) -> AgentState:
        """处理用户输入，分类并拆解任务"""
        user_input = state["user_input"]

        # 分类任务
        task_type = self._classify_task(user_input)

        # 拆解任务
        subtasks = self._decompose_task(user_input, task_type)

        # 更新状态
        state["task_type"] = task_type
        state["subtasks"] = subtasks
        state["status"] = "processing"

        # 添加系统消息
        state["messages"].append({
            "role": "system",
            "content": f"任务已分类为: {task_type}, 拆解为 {len(subtasks)} 个子任务"
        })

        return state

def scheduler_node(state: AgentState) -> AgentState:
    """调度节点函数，用于LangGraph"""
    agent = SchedulerAgent()
    return agent.process(state)