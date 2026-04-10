from typing import TypedDict, List, Dict, Any, Optional


class AgentState(TypedDict):
    """智能体共享状态"""
    # 用户输入
    user_input: str

    # 任务类型："qa"（问答），"tool"（工具），"mixed"（混合）
    task_type: str

    # 任务拆解结果
    subtasks: List[Dict[str, Any]]

    # RAG检索结果
    retrieved_docs: List[str]

    # 工具执行结果
    tool_results: Dict[str, Any]

    # 最终输出
    final_output: str

    # 执行状态
    status: str  # "pending", "processing", "completed", "failed"

    # 错误信息
    error_message: Optional[str]

    # 消息历史（用于对话上下文）
    messages: List[Dict[str, Any]]