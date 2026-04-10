import logging
import sys
from typing import Optional
from datetime import datetime

from src.config.settings import settings


class Logger:
    """日志管理器"""

    def __init__(self, name: str = "enterprise_agent"):
        self.logger = logging.getLogger(name)

        if not self.logger.handlers:
            self._setup_logger()

    def _setup_logger(self):
        """配置日志"""
        self.logger.setLevel(logging.DEBUG if settings.debug else logging.INFO)

        # 控制台处理器
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.DEBUG if settings.debug else logging.INFO)

        # 文件处理器
        file_handler = logging.FileHandler("logs/agent.log", encoding="utf-8")
        file_handler.setLevel(logging.INFO)

        # 格式化器
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        console_handler.setFormatter(formatter)
        file_handler.setFormatter(formatter)

        self.logger.addHandler(console_handler)
        self.logger.addHandler(file_handler)

    def info(self, message: str, **kwargs):
        """信息日志"""
        self.logger.info(message, **kwargs)

    def debug(self, message: str, **kwargs):
        """调试日志"""
        self.logger.debug(message, **kwargs)

    def warning(self, message: str, **kwargs):
        """警告日志"""
        self.logger.warning(message, **kwargs)

    def error(self, message: str, **kwargs):
        """错误日志"""
        self.logger.error(message, **kwargs)

    def critical(self, message: str, **kwargs):
        """严重错误日志"""
        self.logger.critical(message, **kwargs)


# 全局日志实例
logger = Logger()


def log_agent_action(agent_name: str, action: str, details: Optional[dict] = None):
    """记录智能体动作"""
    log_message = f"[{agent_name}] {action}"
    if details:
        import json
        log_message += f" | {json.dumps(details, ensure_ascii=False)}"
    logger.info(log_message)