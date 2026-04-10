import asyncio
import json
from typing import AsyncGenerator
import litellm

from src.agents.graph import agent_graph
from src.agents.state import AgentState
from src.config.settings import settings
from src.utils.logger import logger


async def stream_agent_response(user_input: str) -> AsyncGenerator[str, None]:
    """
    流式返回智能体响应
    """
    try:
        # 第一步：发送开始信号
        yield f"data: {json.dumps({'event': 'start', 'message': '开始处理请求...'})}\n\n"

        # 第二步：执行调度Agent（任务分类）
        from src.agents.scheduler_agent import SchedulerAgent
        scheduler = SchedulerAgent()

        # 创建初始状态
        initial_state = AgentState(
            user_input=user_input,
            task_type='',
            subtasks=[],
            retrieved_docs=[],
            tool_results= {},
            final_output= "",
            status= "pending",
            error_message= None,
            messages=[]
        )

        # 调度处理
        scheduler_state = scheduler.process(initial_state)
        task_type = scheduler_state["task_type"]

        yield f"data: {json.dumps({'event': 'scheduling', 'message': f'任务分类为: {task_type}', 'task_type': task_type})}\n\n"

        # 第三步：根据任务类型处理
        if task_type == "qa" or task_type == "mixed":
            yield f"data: {json.dumps({'event': 'retrieving', 'message': '正在从知识库检索信息...'})}\n\n"

            from src.agents.kb_agent import KnowledgeBaseAgent
            kb_agent = KnowledgeBaseAgent()
            kb_state = kb_agent.process(scheduler_state)

            retrieved_count = len(kb_state["retrieved_docs"])
            yield f"data: {json.dumps({'event': 'retrieved', 'message': f'已检索到 {retrieved_count} 条相关信息'})}\n\n"

            current_state = kb_state
        else:
            current_state = scheduler_state

        # 第四步：工具执行（如果有工具任务）
        if task_type == "tool" or task_type == "mixed":
            # 检查是否有工具任务
            subtasks = current_state.get("subtasks", [])
            has_tool_tasks = any(
                subtask.get("type") in ["search", "tool", "api", "file"]
                for subtask in subtasks
            )

            if has_tool_tasks:
                yield f"data: {json.dumps({'event': 'tool_execution', 'message': '正在执行工具任务...'})}\n\n"

                from src.agents.tool_agent import ToolExecutionAgent
                tool_agent = ToolExecutionAgent()
                tool_state = tool_agent.process(current_state)

                tool_count = len(tool_state["tool_results"])
                yield f"data: {json.dumps({'event': 'tools_completed', 'message': f'已执行 {tool_count} 个工具'})}\n\n"

                current_state = tool_state

        # 第五步：生成最终答案（流式生成）
        yield f"data: {json.dumps({'event': 'generating', 'message': '正在生成最终回答...'})}\n\n"

        # 使用LiteLLM流式生成
        final_prompt = f"""
        基于以下上下文，回答用户问题：{user_input}
        
        请生成一个完整、准确的回答。
        """

        # 流式生成回答
        response = litellm.completion(
            model=settings.litellm_model,
            messages=[
                {"role": "system", "content": "你是一个专业的助手"},
                {"role": "user", "content": final_prompt}
            ],
            stream=True,
            temperature=0.3
        )

        answer_parts = []
        for chunk in response:
            if chunk.choices[0].delta.content:
                content = chunk.choices[0].delta.content
                answer_parts.append(content)
                yield f"data: {json.dumps({'event': 'chunk', 'content': content})}\n\n"

        # 第六步：发送完成信号
        full_answer = "".join(answer_parts)
        yield f"data: {json.dumps({'event': 'complete', 'message': '处理完成', 'answer': full_answer})}\n\n"

    except Exception as e:
        logger.error(f"流式响应错误: {str(e)}")
        yield f"data: {json.dumps({'event': 'error', 'message': f'处理失败: {str(e)}'})}\n\n"


async def generate_simple_stream(user_input: str) -> AsyncGenerator[str, None]:
    """
    简化版流式响应（直接调用完整图）
    """
    # 执行完整图
    result = agent_graph.invoke(user_input)

    # 流式返回结果
    final_answer = result["final_output"]

    # 模拟流式返回
    yield f"data: {json.dumps({'event': 'start', 'message': '开始处理...'})}\n\n"

    # 分块返回答案
    chunk_size = 50
    for i in range(0, len(final_answer), chunk_size):
        chunk = final_answer[i:i + chunk_size]
        yield f"data: {json.dumps({'event': 'chunk', 'content': chunk})}\n\n"
        await asyncio.sleep(0.05)  # 模拟延迟

    yield f"data: {json.dumps({'event': 'complete', 'message': '处理完成'})}\n\n"