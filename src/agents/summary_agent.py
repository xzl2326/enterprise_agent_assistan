import litellm
import json
from typing import Dict, Any

from src.agents.state import AgentState
from src.config.settings import settings
from src.utils.logger import log_agent_action


class SummaryAgent:
    """总结复盘Agent：结果整合、格式化输出、执行日志生成"""

    def __init__(self):
        self.model = settings.litellm_model

    def _generate_final_answer(self, state: AgentState) -> str:
        """生成最终答案"""
        user_input = state["user_input"]
        task_type = state["task_type"]
        retrieved_docs = state.get("retrieved_docs", [])
        tool_results = state.get("tool_results", {})

        # 构建上下文
        context_parts = []

        if retrieved_docs and not any("检索失败" in doc for doc in retrieved_docs):
            context_parts.append("## 知识库信息")
            for i, doc in enumerate(retrieved_docs[:3], 1):
                context_parts.append(f"{i}. {doc[:200]}...")

        if tool_results:
            context_parts.append("## 工具执行结果")
            for key, result in tool_results.items():
                if isinstance(result, dict) and "result" in result:
                    tool_result = result["result"]
                    if isinstance(tool_result, str):
                        context_parts.append(f"- {key}: {tool_result[:150]}...")
                    else:
                        context_parts.append(f"- {key}: {str(tool_result)[:150]}...")

        context = "\n\n".join(context_parts) if context_parts else "无额外上下文信息"

        prompt = f"""
        用户问题：{user_input}
        
        任务类型：{task_type}
        
        可用上下文信息：
        {context}
        
        请基于以上信息，生成一个完整、准确、友好的回答。
        要求：
        1. 直接回答用户问题
        2. 如果使用了知识库信息或工具结果，简要说明信息来源
        3. 回答要清晰、有条理
        4. 用中文回答
        """

        response = litellm.completion(
            model=self.model,
            messages=[
                {"role": "system", "content": "你是一个专业的助手，负责整合信息并给出最终回答"},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3
        )

        return response.choices[0].message.content

    def _generate_execution_log(self, state: AgentState) -> Dict[str, Any]:
        """生成执行日志"""
        return {
            "user_input": state["user_input"],
            "task_type": state["task_type"],
            "subtasks": state.get("subtasks", []),
            "retrieved_docs_count": len(state.get("retrieved_docs", [])),
            "tool_count": len(state.get("tool_results", {})),
            "status": state["status"],
            "timestamp": "生成日志时间",
            "messages": state["messages"]
        }

    def process(self, state: AgentState) -> AgentState:
        """处理总结复盘"""
        # 生成最终答案
        final_answer = self._generate_final_answer(state)

        # 生成执行日志
        execution_log = self._generate_execution_log(state)

        # 更新状态
        state["final_output"] = final_answer
        state["status"] = "completed"
        state["tool_results"]["execution_log"] = execution_log

        # 记录日志
        log_agent_action("SummaryAgent", "生成最终答案并完成处理", {
            "answer_length": len(final_answer),
            "task_type": state["task_type"]
        })

        # 添加最终消息
        state["messages"].append({
            "role": "assistant",
            "content": final_answer
        })

        return state


def summary_node(state: AgentState) -> AgentState:
    """总结节点函数，用于LangGraph"""
    agent = SummaryAgent()
    return agent.process(state)