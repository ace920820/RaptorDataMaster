"""
pytest配置文件
"""
import os
import sys
import pytest

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

@pytest.fixture(autouse=True)
def setup_test_env():
    """设置测试环境"""
    # 设置测试环境变量
    os.environ["TESTING"] = "1"
    yield
    # 清理环境变量
    os.environ.pop("TESTING", None)
