"""
企业级多角色智能任务助理Agent - 主入口文件

为什么怎么写：
1. 作为FastAPI应用入口，需要提供完整的Web服务功能，包括生命周期管理、CORS、异常处理等
2. 采用模块化设计，分离配置、路由、业务逻辑，便于维护和扩展
3. 使用异步上下文管理器管理应用生命周期，确保资源正确初始化和释放

怎么写的作用是什么：
1. 提供REST ful API接口，支持HTTP请求处理和响应
2. 集成多智能体系统，通过API调用触发智能体协作流程
3. 支持流式响应，满足实时交互需求
4. 提供健康检查、文档上传、聊天等核心功能
"""

import os
import uvicorn
from typing import Any, AsyncGenerator
from fastapi import FastAPI, HTTPException,requests
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager

from src.api.routes import router as api_router
from src.config.settings import settings
from src.utils.logger import logger


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[dict[Any, Any], Any]:
    """
    应用生命周期管理

    为什么怎么写：
    1. 使用@asynccontextmanager装饰器实现异步上下文管理器，符合FastAPI生命周期管理规范
    2. 在应用启动和关闭时执行初始化和清理操作，确保资源管理的一致性
    3. 通过logger记录启动信息，便于监控和调试

    怎么写的作用是什么：
    1. 启动时创建必要的目录结构（logs/, data/），确保文件存储可用
    2. 输出关键配置信息（模型、向量库、调试模式），帮助快速了解运行环境
    3. 提供优雅地启动和关闭流程，支持资源预分配和释放
    """
    # 启动时
    logger.info("企业级智能任务助理启动中...")
    logger.info(f"使用模型: {settings.litellm_model}")
    logger.info(f"向量数据库: {settings.qdrant_url}")
    logger.info(f"调试模式: {settings.debug}")

    # 设置豆包API Key环境变量
    if hasattr(settings, 'VOLCENGINE_API_KEY') and settings.VOLCENGINE_API_KEY:
        os.environ['VOLCENGINE_API_KEY'] = settings.VOLCENGINE_API_KEY
        logger.info("已设置 VOLCENGINE_API_KEY 环境变量")

    # 兼容旧配置
    if hasattr(settings, 'doubao_api_key') and settings.doubao_api_key:
        os.environ['VOLCENGINE_API_KEY'] = settings.doubao_api_key
        logger.info("已设置 VOLCENGINE_API_KEY 环境变量(兼容)")

    # 创建日志目录
    os.makedirs("logs", exist_ok=True)

    # 创建数据目录
    os.makedirs("data", exist_ok=True)

    yield {}

    # 关闭时
    logger.info("企业级智能任务助理关闭中...")


# 为什么怎么写：使用FastAPI创建Web应用，设置应用元信息便于API文档生成
# 怎么写的作用是什么：提供Swagger UI自动文档，支持OpenAPI标准，便于前端集成和测试
# 创建FastAPI应用
app = FastAPI(
    title="企业级多角色智能任务助理Agent",
    description="基于LangGraph多智能体架构的企业级AI助手",
    version="1.0.0",
    lifespan=lifespan
)

# 为什么怎么写：在调试模式下允许所有跨域请求，便于前端开发；生产环境限制来源
# 怎么写的作用是什么：解决浏览器跨域问题，支持前后端分离部署，同时保障生产环境安全
# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.debug else [],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 为什么怎么写：使用FastAPI异常处理器捕获所有未处理异常，避免服务崩溃
# 怎么写的作用是什么：提供友好的错误响应，调试模式下显示详细错误，生产环境隐藏细节
# 全局异常处理
@app.exception_handler(Exception)
async def global_exception_handler(requests,exc: Exception):
    # 如果是HTTPException，直接返回其响应
    if isinstance(exc, HTTPException):
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "success": False,
                "error": exc.detail,
                "message": str(exc.detail)
            }
        )

    logger.error(f"全局异常: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": "服务器内部错误",
            "message": str(exc) if settings.debug else "请稍后重试"
        }
    )

# 为什么怎么写：挂载静态文件目录，提供前端资源访问能力
# 怎么写的作用是什么：支持前端页面、图片、CSS/JS等静态资源服务，便于部署完整应用
# 挂载静态文件
app.mount("/static", StaticFiles(directory="static"), name="static")

# 为什么怎么写：模块化路由设计，将API路由分离到单独文件，保持主文件简洁
# 怎么写的作用是什么：实现路由分层管理，便于API版本控制和功能模块扩展
# 注册路由
app.include_router(api_router)

# 根路由
@app.get("/")
async def root():
    """
    根路由 - 返回前端页面
    为什么这么写：
    - 访问根路径时直接返回前端HTML页面
    - 提供用户友好的访问体验
    """
    index_path = os.path.join("static", "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    else:
        # 如果HTML文件不存在，返回API信息
        return {
            "service": "企业级多角色智能任务助理Agent",
            "version": "1.0.0",
            "status": "运行中",
            "endpoints": {
                "chat": "/api/v1/chat",
                "chat_stream": "/api/v1/chat/stream",
                "knowledge_upload": "/api/v1/knowledge/upload",
                "health": "/api/v1/health",
                "tools": "/api/v1/tools",
                "docs": "/docs",
                "frontend": "/static/index.html"
            }
        }

# API信息路由（保留原JSON接口）
@app.get("/api")
async def api_info():
    return {
        "service": "企业级多角色智能任务助理Agent",
        "version": "1.0.0",
        "status": "运行中",
        "endpoints": {
            "chat": "/api/v1/chat",
            "chat_stream": "/api/v1/chat/stream",
            "knowledge_upload": "/api/v1/knowledge/upload",
            "health": "/api/v1/health",
            "tools": "/api/v1/tools",
            "docs": "/docs"
        }
    }


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.app_host,
        port=settings.app_port,
        reload=settings.debug,
        log_level="debug" if settings.debug else "info"
    )