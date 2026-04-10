import sys
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

# 添加src目录到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from main import app


@pytest.fixture
def client():
    """提供测试客户端"""
    with TestClient(app) as test_client:
        yield test_client