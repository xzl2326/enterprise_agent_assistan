import os
import json
import csv
from typing import List, Dict, Any
from datetime import datetime


def read_file(file_path: str) -> str:
    """
    读取文件内容

    Args:
        file_path: 文件路径

    Returns:
        文件内容字符串
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        return f"读取文件失败: {str(e)}"


def write_file(file_path: str, content: str) -> str:
    """
    写入文件

    Args:
        file_path: 文件路径
        content: 要写入的内容

    Returns:
        操作结果
    """
    try:
        # 确保目录存在
        os.makedirs(os.path.dirname(file_path), exist_ok=True)

        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return f"文件已成功写入: {file_path}"
    except Exception as e:
        return f"写入文件失败: {str(e)}"


def list_files(directory: str, extension: str = None) -> List[str]:
    """
    列出目录中的文件

    Args:
        directory: 目录路径
        extension: 文件扩展名过滤

    Returns:
        文件路径列表
    """
    try:
        if not os.path.exists(directory):
            return [f"目录不存在: {directory}"]

        files = []
        for file in os.listdir(directory):
            file_path = os.path.join(directory, file)
            if os.path.isfile(file_path):
                if extension is None or file.endswith(extension):
                    files.append(file_path)
        return files
    except Exception as e:
        return [f"列出文件失败: {str(e)}"]


def analyze_file(file_path: str) -> Dict[str, Any]:
    """
    分析文件信息

    Args:
        file_path: 文件路径

    Returns:
        文件信息字典
    """
    try:
        if not os.path.exists(file_path):
            return {"error": f"文件不存在: {file_path}"}

        stat_info = os.stat(file_path)
        file_size = stat_info.st_size
        created_time = datetime.fromtimestamp(stat_info.st_ctime)
        modified_time = datetime.fromtimestamp(stat_info.st_mtime)

        # 获取文件扩展名
        _, ext = os.path.splitext(file_path)

        return {
            "path": file_path,
            "size_bytes": file_size,
            "size_human": f"{file_size / 1024:.2f} KB",
            "created": created_time.strftime("%Y-%m-%d %H:%M:%S"),
            "modified": modified_time.strftime("%Y-%m-%d %H:%M:%S"),
            "extension": ext,
            "exists": True
        }
    except Exception as e:
        return {"error": f"分析文件失败: {str(e)}"}