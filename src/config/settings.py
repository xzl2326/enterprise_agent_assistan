
from typing import Optional

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """应用配置设置"""

    # 大模型配置
    VOLCENGINE_API_KEY: str = "9c9a1c62-601c-47f9-95e0-3a9ab6a667e7"
    litellm_model: str = "volcengine/doubao-seed-2-0-lite-260215"  # 默认模型，添加提供者前缀
    litellm_api_base: Optional[str] = None  # Litellm API基础URL，默认为None使用官方

    # Qdrant配置
    qdrant_url: str = "http://localhost:6333"
    qdrant_collection_name: str = "enterprise_kb"

    # LangSmith监控配置
    langchain_tracing_v2: bool = False
    langchain_api_key: Optional[str] = None
    langchain_project: str = "enterprise-agent-assistant"
    langchain_endpoint: Optional[str] = None

    # 应用配置
    app_host: str = "127.0.0.1"
    app_port: int = 8000
    debug: bool = True

    # 文档处理配置
    chunk_size: int = 1000
    chunk_overlap: int = 200

    embedding_local_only: bool = False
    embedding_cache_dir: Optional[str] = "./models"
    embedding_timeout: int = 30
    huggingface_mirror: Optional[str] = None

    # ========== 阿里云百炼 配置 ==========
    # 大模型
    # 百炼通用模型
    dashscope_api_key: str = "sk-9e6151f094774f8b928c0e578076e03c"  # 你自己的百炼 API Key

    # 嵌入模型（向量模型）
    embedding_provider: str = "aliyun"
    embedding_model: str = "text-embedding-v3"
    embedding_dimension: int = 1024


# 全局配置实例
settings = Settings()
