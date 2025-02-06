"""
知识库管理系统的单元测试
包含以下测试模块：
1. 存储模块测试（TestStorage）
2. 上传模块测试（TestUploader）
3. API接口测试（TestAPI）
"""
import os
import json
import sys
import pytest
import logging
from datetime import datetime
from fastapi.testclient import TestClient
from fastapi import UploadFile
from unittest.mock import Mock, patch, mock_open

# 配置日志输出
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 添加项目根目录到Python路径
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(PROJECT_ROOT)
logger.info(f"项目根目录: {PROJECT_ROOT}")

# 设置测试环境变量
os.environ["TESTING"] = "1"
logger.info("已设置测试环境变量 TESTING=1")

from knowledge_base.api import app
from knowledge_base.storage import DocumentStorage
from knowledge_base.upload import FileUploader
from knowledge_base.manage import DocumentManager

# 测试客户端
client = TestClient(app)

# 测试数据目录
TEST_DATA_DIR = os.path.join(os.path.dirname(__file__), "test_data")
os.makedirs(TEST_DATA_DIR, exist_ok=True)
logger.info(f"测试数据目录: {TEST_DATA_DIR}")

@pytest.fixture(autouse=True)
def mock_stdin():
    """模拟stdin输入，自动回答'y'"""
    with patch('builtins.input', return_value='y'):
        yield

@pytest.fixture(autouse=True)
def cleanup_test_data():
    """清理测试数据的夹具
    
    在每个测试前后自动运行，确保测试数据目录的清洁
    """
    logger.info("准备清理测试数据目录")
    yield
    if os.path.exists(TEST_DATA_DIR):
        for file in os.listdir(TEST_DATA_DIR):
            try:
                file_path = os.path.join(TEST_DATA_DIR, file)
                os.remove(file_path)
                logger.info(f"已删除测试文件: {file}")
            except Exception as e:
                logger.error(f"删除文件失败: {file}, 错误: {str(e)}")

@pytest.fixture
def test_storage():
    """创建测试用的存储实例
    
    Returns:
        DocumentStorage: 配置为使用测试数据目录的存储实例
    """
    logger.info("创建测试存储实例")
    storage = DocumentStorage(storage_dir=TEST_DATA_DIR)
    logger.info(f"测试存储实例创建成功，使用目录: {TEST_DATA_DIR}")
    return storage

@pytest.fixture
def test_uploader():
    """创建测试用的上传器实例
    
    Returns:
        FileUploader: 配置为使用测试数据目录的上传器实例
    """
    logger.info("创建测试上传器实例")
    uploader = FileUploader(upload_dir=TEST_DATA_DIR)
    logger.info(f"测试上传器实例创建成功，使用目录: {TEST_DATA_DIR}")
    return uploader

@pytest.fixture
def test_manager():
    """创建测试用的文档管理器实例
    
    使用mock模拟RetrievalAugmentation，避免实际调用外部服务
    
    Returns:
        DocumentManager: 配置为使用测试环境的文档管理器实例
    """
    logger.info("创建测试文档管理器实例")
    with patch('knowledge_base.manage.RetrievalAugmentation') as mock_ra:
        # 模拟RetrievalAugmentation的行为
        instance = mock_ra.return_value
        instance.add_documents.return_value = None
        instance.get_all_nodes_info.return_value = {
            "leaf_nodes": [],
            "summary_nodes": {},
            "num_layers": 1,
            "total_nodes": 0
        }
        logger.info("已模拟RetrievalAugmentation实例")
        
        # 创建管理器实例
        manager = DocumentManager(storage_dir=TEST_DATA_DIR)
        logger.info("测试文档管理器实例创建成功")
        yield manager

class TestStorage:
    """存储模块测试"""
    
    def test_save_document(self, test_storage):
        """测试保存文档"""
        logger.info("测试保存文档")
        doc_id = "test_doc_1"
        content = "这是测试文档内容"
        tree_data = {
            "leaf_nodes": [],
            "summary_nodes": {},
            "num_layers": 1,
            "total_nodes": 0
        }
        
        # 保存文档
        result = test_storage.save_document(doc_id, content, tree_data)
        assert result == True
        logger.info("文档保存成功")
        
        # 验证文件是否存在
        doc_path = os.path.join(TEST_DATA_DIR, f"{doc_id}.txt")
        tree_path = os.path.join(TEST_DATA_DIR, f"{doc_id}_tree.json")
        assert os.path.exists(doc_path)
        assert os.path.exists(tree_path)
        logger.info("文档文件存在")
        
        # 验证内容是否正确
        with open(doc_path, "r", encoding="utf-8") as f:
            saved_content = f.read()
        assert saved_content == content
        logger.info("文档内容正确")
        
        with open(tree_path, "r", encoding="utf-8") as f:
            saved_tree = json.load(f)
        assert saved_tree == tree_data
        logger.info("文档树结构正确")
    
    def test_get_document(self, test_storage):
        """测试获取文档"""
        logger.info("测试获取文档")
        # 先保存一个测试文档
        doc_id = "test_doc_2"
        content = "测试文档2的内容"
        tree_data = {
            "leaf_nodes": [],
            "summary_nodes": {},
            "num_layers": 1,
            "total_nodes": 0
        }
        test_storage.save_document(doc_id, content, tree_data)
        
        # 获取文档
        doc_info = test_storage.get_document(doc_id)
        assert doc_info is not None
        assert doc_info["content"] == content
        assert doc_info["tree"] == tree_data
        logger.info("文档获取成功")
    
    def test_delete_document(self, test_storage):
        """测试删除文档"""
        logger.info("测试删除文档")
        # 先保存一个测试文档
        doc_id = "test_doc_3"
        content = "测试文档3的内容"
        tree_data = {
            "leaf_nodes": [],
            "summary_nodes": {},
            "num_layers": 1,
            "total_nodes": 0
        }
        test_storage.save_document(doc_id, content, tree_data)
        
        # 删除文档
        result = test_storage.delete_document(doc_id)
        assert result == True
        logger.info("文档删除成功")
        
        # 验证文件是否已删除
        doc_path = os.path.join(TEST_DATA_DIR, f"{doc_id}.txt")
        tree_path = os.path.join(TEST_DATA_DIR, f"{doc_id}_tree.json")
        assert not os.path.exists(doc_path)
        assert not os.path.exists(tree_path)
        logger.info("文档文件已删除")

class TestUploader:
    """上传模块测试"""
    
    @pytest.mark.asyncio
    async def test_save_upload_file(self, test_uploader):
        """测试保存上传文件"""
        logger.info("测试保存上传文件")
        # 模拟上传文件
        text = "这是测试文件内容"
        file_content = text.encode('utf-8')
        mock_file = Mock(spec=UploadFile)
        mock_file.filename = "test.txt"
        mock_file.read = Mock(return_value=file_content)
        
        # 保存文件
        file_id = await test_uploader.save_upload_file(mock_file)
        assert file_id is not None
        logger.info("文件保存成功")
        
        # 验证文件是否保存成功
        saved_path = os.path.join(TEST_DATA_DIR, f"{file_id}.txt")
        assert os.path.exists(saved_path)
        with open(saved_path, "rb") as f:
            saved_content = f.read()
        assert saved_content == file_content
        logger.info("文件内容正确")
    
    def test_read_file_content(self, test_uploader):
        """测试读取文件内容"""
        logger.info("测试读取文件内容")
        # 创建测试文件
        file_id = "test_file_1"
        content = "测试文件内容"
        with open(os.path.join(TEST_DATA_DIR, f"{file_id}.txt"), "w", encoding="utf-8") as f:
            f.write(content)
        
        # 读取内容
        read_content = test_uploader.read_file_content(file_id)
        assert read_content == content
        logger.info("文件内容读取成功")

class TestAPI:
    """API接口测试"""
    
    def test_upload_document(self):
        """测试文档上传接口"""
        logger.info("测试文档上传接口")
        # 创建测试文件
        text = "测试文档内容"
        file_content = text.encode('utf-8')
        files = {
            "file": ("test.txt", file_content, "text/plain")
        }
        
        # 上传文件
        response = client.post("/documents/upload", files=files)
        assert response.status_code == 200
        assert "document_id" in response.json()
        logger.info("文档上传成功")
    
    def test_list_documents(self):
        """测试获取文档列表接口"""
        logger.info("测试获取文档列表接口")
        response = client.get("/documents")
        assert response.status_code == 200
        assert isinstance(response.json(), list)
        logger.info("文档列表获取成功")
    
    def test_get_document(self):
        """测试获取文档详情接口"""
        logger.info("测试获取文档详情接口")
        # 先上传一个文档
        files = {
            "file": ("test.txt", "测试文档内容".encode('utf-8'), "text/plain")
        }
        upload_response = client.post("/documents/upload", files=files)
        assert upload_response.status_code == 200
        doc_id = upload_response.json()["document_id"]
        
        # 获取文档详情
        response = client.get(f"/documents/{doc_id}")
        assert response.status_code == 200
        assert "content" in response.json()
        assert "tree" in response.json()
        logger.info("文档详情获取成功")
        
        # 测试获取不存在的文档
        response = client.get("/documents/non_existent_id")
        assert response.status_code == 404
        logger.info("获取不存在文档返回404")
    
    def test_delete_document(self):
        """测试删除文档接口"""
        logger.info("测试删除文档接口")
        # 先上传一个文档
        files = {
            "file": ("test.txt", "测试文档内容".encode('utf-8'), "text/plain")
        }
        upload_response = client.post("/documents/upload", files=files)
        assert upload_response.status_code == 200
        doc_id = upload_response.json()["document_id"]
        
        # 删除文档
        response = client.delete(f"/documents/{doc_id}")
        assert response.status_code == 200
        assert response.json()["message"] == "删除成功"
        logger.info("文档删除成功")
        
        # 验证文档已被删除
        response = client.get(f"/documents/{doc_id}")
        assert response.status_code == 404
        logger.info("文档已被删除")
        
        # 测试删除不存在的文档
        response = client.delete("/documents/non_existent_id")
        assert response.status_code == 404
        logger.info("删除不存在文档返回404")

if __name__ == "__main__":
    pytest.main(["-v", "tests/test_knowledge_base.py"])
