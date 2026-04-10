from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from typing import Dict, Any
from src.agents.graph import agent_graph
from src.api.stream_response import stream_agent_response
from src.rag.retriever import add_documents_to_store, clear_vector_store
from src.rag.document_parser import document_parser
from src.utils.logger import logger

router = APIRouter(prefix="/api/v1", tags=["agent"])


@router.post("/chat")
async def chat_endpoint(request: Dict[str, Any]):
    """
    聊天接口 - 处理用户请求并返回智能体响应
    """
    try:
        user_input = request.get("message", "")
        if not user_input:
            raise HTTPException(status_code=400, detail="消息不能为空")

        logger.info(f"收到用户请求: {user_input[:100]}...")

        # 执行智能体图
        result = agent_graph.invoke(user_input)

        return {
            "success": True,
            "data": {
                "answer": result["final_output"],
                "task_type": result["task_type"],
                "status": result["status"],
                "retrieved_docs_count": len(result.get("retrieved_docs", [])),
                "tool_count": len(result.get("tool_results", {})),
                "messages": result["messages"]
            }
        }

    except Exception as e:
        logger.error(f"聊天接口错误: {str(e)}")
        raise HTTPException(status_code=500, detail=f"处理失败: {str(e)}")


@router.post("/chat/stream")
async def chat_stream_endpoint(request: Dict[str, Any]):
    """
    流式聊天接口 - 使用SSE返回实时响应
    """
    user_input = request.get("message", "")
    if not user_input:
        raise HTTPException(status_code=400, detail="消息不能为空")

    return StreamingResponse(
        stream_agent_response(user_input),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


@router.post("/knowledge/upload")
async def upload_knowledge(request: Dict[str, Any]):
    """
    上传文档到知识库
    """
    try:
        file_path = request.get("file_path")
        if not file_path:
            raise HTTPException(status_code=400, detail="文件路径不能为空")

        logger.info(f"上传文档到知识库: {file_path}")

        # 处理文档
        documents = document_parser.process_file(file_path)

        # 添加到向量存储
        add_documents_to_store(documents)

        return {
            "success": True,
            "data": {
                "file_path": file_path,
                "chunks_count": len(documents),
                "message": f"成功添加 {len(documents)} 个文档块到知识库"
            }
        }

    except Exception as e:
        logger.error(f"上传文档错误: {str(e)}")
        raise HTTPException(status_code=500, detail=f"上传失败: {str(e)}")


@router.post("/knowledge/batch-upload")
async def batch_upload_knowledge(request: Dict[str, Any]):
    """
    批量上传目录下的文档到知识库
    """
    try:
        directory_path = request.get("directory_path")
        if not directory_path:
            raise HTTPException(status_code=400, detail="目录路径不能为空")

        logger.info(f"批量上传文档到知识库: {directory_path}")

        # 处理目录
        documents = document_parser.process_directory(directory_path)

        # 添加到向量存储
        add_documents_to_store(documents)

        return {
            "success": True,
            "data": {
                "directory_path": directory_path,
                "chunks_count": len(documents),
                "message": f"成功添加 {len(documents)} 个文档块到知识库"
            }
        }

    except Exception as e:
        logger.error(f"批量上传文档错误: {str(e)}")
        raise HTTPException(status_code=500, detail=f"批量上传失败: {str(e)}")


@router.delete("/knowledge/clear")
async def clear_knowledge():
    """
    清空知识库
    """
    try:
        clear_vector_store()

        return {
            "success": True,
            "data": {
                "message": "知识库已清空"
            }
        }

    except Exception as e:
        logger.error(f"清空知识库错误: {str(e)}")
        raise HTTPException(status_code=500, detail=f"清空失败: {str(e)}")


@router.get("/health")
async def health_check():
    """
    健康检查接口
    """
    return {
        "status": "healthy",
        "service": "enterprise-agent-assistant",
        "version": "1.0.0"
    }


@router.get("/tools")
async def list_tools():
    """
    列出可用工具
    """
    from src.agents.tool_agent import ToolExecutionAgent
    agent = ToolExecutionAgent()

    tools_info = {}
    for name, info in agent.available_tools.items():
        tools_info[name] = {
            "description": info["description"],
            "parameters": info["parameters"]
        }

    return {
        "success": True,
        "data": {
            "tools": tools_info,
            "count": len(tools_info)
        }
    }