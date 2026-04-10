from langgraph.graph import StateGraph, END
from typing import Literal

from src.agents.state import AgentState
from src.agents.scheduler_agent import scheduler_node
from src.agents.kb_agent import kb_node
from src.agents.tool_agent import tool_node
from src.agents.summary_agent import summary_node


class AgentGraph:
    """智能体图：协调多智能体协作"""
    
    def __init__(self):
        self.graph = StateGraph(AgentState)
        self._build_graph()
        
    def _build_graph(self):
        """构建智能体图"""
        
        # 添加节点
        self.graph.add_node("scheduler", scheduler_node)
        self.graph.add_node("knowledge_base", kb_node)
        self.graph.add_node("tool_executor", tool_node)
        self.graph.add_node("summarizer", summary_node)
        
        # 设置入口点
        self.graph.set_entry_point("scheduler")
        
        # 定义条件路由
        def route_after_scheduler(state: AgentState) -> Literal["knowledge_base", "tool_executor", "summarizer"]:
            """调度后路由决策"""
            task_type = state.get("task_type", "mixed")
            
            if task_type == "qa":
                return "knowledge_base"
            elif task_type == "tool":
                return "tool_executor"
            else:  # mixed
                return "knowledge_base"  # 混合任务先走知识库
        
        def route_after_knowledge(state: AgentState) -> Literal["tool_executor", "summarizer"]:
            """知识库处理后路由决策"""
            task_type = state.get("task_type", "mixed")
            subtasks = state.get("subtasks", [])
            
            # 检查是否有工具任务
            has_tool_tasks = any(
                subtask.get("type") in ["search", "tool", "api", "file"] 
                for subtask in subtasks
            )
            
            if task_type == "mixed" and has_tool_tasks:
                return "tool_executor"
            else:
                return "summarizer"
        
        def route_after_tools(state: AgentState) -> Literal["summarizer"]:
            """工具处理后路由决策"""
            return "summarizer"
        
        # 添加条件边
        self.graph.add_conditional_edges(
            "scheduler",
            route_after_scheduler,
            {
                "knowledge_base": "knowledge_base",
                "tool_executor": "tool_executor",
                "summarizer": "summarizer"
            }
        )
        
        self.graph.add_conditional_edges(
            "knowledge_base",
            route_after_knowledge,
            {
                "tool_executor": "tool_executor",
                "summarizer": "summarizer"
            }
        )
        
        self.graph.add_edge("tool_executor", "summarizer")
        self.graph.add_edge("summarizer", END)
        
        # 编译图
        self.compiled_graph = self.graph.compile()
    
    def invoke(self, user_input: str) -> AgentState:
        """执行图"""
        # 初始化状态
        initial_state: AgentState = {
            "user_input": user_input,
            "task_type": "",
            "subtasks": [],
            "retrieved_docs": [],
            "tool_results": {},
            "final_output": "",
            "status": "pending",
            "error_message": None,
            "messages": []
        }
        
        # 执行图
        result = self.compiled_graph.invoke(initial_state)
        
        return result


# 全局图实例
agent_graph = AgentGraph()