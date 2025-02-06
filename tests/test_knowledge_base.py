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
from unittest.mock import Mock, patch, mock_open, MagicMock

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
def mock_ra():
    """模拟RetrievalAugmentation"""
    with patch('knowledge_base.storage.RetrievalAugmentation') as mock_ra:
        instance = mock_ra.return_value
        # 模拟tree属性
        instance.tree = MagicMock()
        instance.tree.num_layers = 1
        instance.tree.all_nodes = {
            0: MagicMock(text="节点0", layer=0, children=[1, 2]),
            1: MagicMock(text="节点1", layer=1),
            2: MagicMock(text="节点2", layer=1)
        }
        instance.tree.leaf_nodes = {1, 2}
        
        # 模拟方法
        instance.add_documents.return_value = None
        instance.save.return_value = None
        yield instance

@pytest.fixture
def test_storage():
    """创建测试用的存储实例
    
    Returns:
        DocumentStorage: 配置为使用测试数据目录的存储实例
    """
    logger.info("创建测试存储实例")
    storage = DocumentStorage(
        storage_dir=TEST_DATA_DIR
    )
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

class TestStorage:
    """存储模块测试"""
    
    def test_add_document(self, test_storage, mock_ra):
        """测试添加文档"""
        logger.info("测试添加文档")
        doc_id = "test_doc_1"
        content = "这是测试文档内容"
        
        # 添加文档
        result = test_storage.add_document(doc_id, content)
        assert result == True
        logger.info("文档添加成功")
        
        # 验证文件是否存在
        doc_path = os.path.join(TEST_DATA_DIR, f"{doc_id}.txt")
        assert os.path.exists(doc_path)
        logger.info("文档文件存在")
        
        # 验证内容是否正确
        with open(doc_path, "r", encoding="utf-8") as f:
            saved_content = f.read()
        assert saved_content == content
        logger.info("文档内容正确")
        
        # 验证RA方法是否被调用
        mock_ra.add_documents.assert_called_once_with(content)
        mock_ra.save.assert_called_once()
        logger.info("RA方法调用正确")
    
    def test_get_document(self, test_storage, mock_ra):
        """测试获取文档"""
        logger.info("测试获取文档")
        # 先添加一个测试文档
        doc_id = "test_doc_2"
        content = "测试文档2的内容"
        test_storage.add_document(doc_id, content)
        
        # 获取文档
        doc_info = test_storage.get_document(doc_id)
        assert doc_info is not None
        assert doc_info["content"] == content
        assert "tree" in doc_info
        assert "nodes" in doc_info["tree"]
        assert "edges" in doc_info["tree"]
        logger.info("文档获取成功")
    
    def test_delete_document(self, test_storage):
        """测试删除文档"""
        logger.info("测试删除文档")
        # 先添加一个测试文档
        doc_id = "test_doc_3"
        content = "测试文档3的内容"
        test_storage.add_document(doc_id, content)
        
        # 删除文档
        result = test_storage.delete_document(doc_id)
        assert result == True
        logger.info("文档删除成功")
        
        # 验证文件是否已删除
        doc_path = os.path.join(TEST_DATA_DIR, f"{doc_id}.txt")
        assert not os.path.exists(doc_path)
        logger.info("文档文件已删除")
    
    def test_update_document_node(self, test_storage, mock_ra):
        """测试更新文档节点"""
        logger.info("测试更新文档节点")
        doc_id = "test_doc_4"
        content = "测试文档4的内容"
        test_storage.add_document(doc_id, content)
        
        # 更新节点
        node_id = 1
        new_text = "更新后的节点内容"
        result = test_storage.update_document_node(doc_id, node_id, new_text)
        assert result == True
        logger.info("节点更新成功")
        
        # 验证RA.save是否被调用
        mock_ra.save.assert_called()
        logger.info("RA.save方法调用正确")
    
    def test_get_tree_info(self, test_storage, mock_ra):
        """测试获取树信息"""
        logger.info("测试获取树信息")
        info = test_storage.get_tree_info()
        assert info["num_layers"] == 1
        assert info["total_nodes"] == 3
        assert info["leaf_nodes"] == 2
        assert info["summary_nodes"] == 1
        logger.info("树信息获取成功")

class TestUploader:
    """上传模块测试"""
    
    async def test_upload_file(self, test_uploader):
        """测试文件上传"""
        logger.info("测试文件上传")
        # 创建测试文件
        content = "测试文件内容"
        file = Mock(spec=UploadFile)
        file.read.return_value = content
        
        # 上传文件
        file_id = await test_uploader.upload_file(file)
        assert file_id is not None
        logger.info("文件上传成功")
        
        # 验证文件是否存在
        file_path = os.path.join(TEST_DATA_DIR, f"{file_id}.txt")
        assert os.path.exists(file_path)
        logger.info("文件存在")
        
        # 验证内容是否正确
        with open(file_path, "rb") as f:
            saved_content = f.read()
        assert saved_content == content
        logger.info("文件内容正确")
    
    def test_read_file_content(self, test_uploader):
        """测试读取文件内容"""
        logger.info("测试读取文件内容")
        # 创建测试文件
        file_id = "test_file"
        content = "测试文件内容"
        file_path = os.path.join(TEST_DATA_DIR, f"{file_id}.txt")
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
        
        # 读取内容
        read_content = test_uploader.read_file_content(file_id)
        assert read_content == content
        logger.info("文件内容读取成功")

class TestAPI:
    """API接口测试"""
    
    async def test_upload_document(self):
        """测试文档上传接口"""
        logger.info("测试文档上传接口")
        # 创建测试文件
        content = "测试文档内容"
        files = {"file": ("test.txt", content, "text/plain")}
        
        # 发送请求
        response = client.post("/documents/upload", files=files)
        assert response.status_code == 200
        assert "id" in response.json()
        logger.info("文档上传接口测试成功")
    
    def test_get_document(self):
        """测试获取文档接口"""
        logger.info("测试获取文档详情接口")
        # 先上传一个文档
        content = "测试文档内容"
        files = {"file": ("test.txt", content, "text/plain")}
        upload_response = client.post("/documents/upload", files=files)
        doc_id = upload_response.json()["id"]
        
        # 获取文档
        response = client.get(f"/documents/{doc_id}")
        assert response.status_code == 200
        assert response.json()["id"] == doc_id
        assert "content" in response.json()
        assert "tree" in response.json()
        logger.info("文档获取接口测试成功")
    
    def test_delete_document(self):
        """测试删除文档接口"""
        logger.info("测试删除文档接口")
        # 先上传一个文档
        content = "测试文档内容"
        files = {"file": ("test.txt", content, "text/plain")}
        upload_response = client.post("/documents/upload", files=files)
        doc_id = upload_response.json()["id"]
        
        # 删除文档
        response = client.delete(f"/documents/{doc_id}")
        assert response.status_code == 200
        assert response.json()["message"] == "删除成功"
        logger.info("文档删除接口测试成功")
    
    def test_update_document_node(self):
        """测试更新文档节点接口"""
        logger.info("测试更新文档节点接口")
        # 先上传一个文档
        content = "测试文档内容"
        files = {"file": ("test.txt", content, "text/plain")}
        upload_response = client.post("/documents/upload", files=files)
        doc_id = upload_response.json()["id"]
        
        # 更新节点
        node_id = "1"
        new_text = "更新后的节点内容"
        response = client.put(
            f"/documents/{doc_id}/nodes/{node_id}",
            json={"text": new_text}
        )
        assert response.status_code == 200
        assert response.json()["message"] == "更新成功"
        logger.info("节点更新接口测试成功")
    
    def test_list_documents(self):
        """测试获取文档列表接口"""
        logger.info("测试获取文档列表接口")
        response = client.get("/documents")
        assert response.status_code == 200
        assert isinstance(response.json(), list)
        logger.info("文档列表接口测试成功")
    
    def test_get_tree_info(self):
        """测试获取树信息接口"""
        logger.info("测试获取树信息接口")
        response = client.get("/tree/info")
        assert response.status_code == 200
        assert "num_layers" in response.json()
        assert "total_nodes" in response.json()
        assert "leaf_nodes" in response.json()
        assert "summary_nodes" in response.json()
        logger.info("树信息接口测试成功")

if __name__ == "__main__":
    pytest.main(["-v", "tests/test_knowledge_base.py"])
