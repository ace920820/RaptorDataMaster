"""
管理模块 - 负责文档的增删改查
"""
import sys
import os
from typing import Dict, List, Optional
import logging

# 添加项目根目录到Python路径
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(PROJECT_ROOT)

from raptor import RetrievalAugmentation
from .storage import DocumentStorage
from .upload import FileUploader

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DocumentManager:
    def __init__(self, storage_dir: Optional[str] = None):
        """初始化文档管理器
        
        Args:
            storage_dir: 存储目录路径，如果不指定则使用默认目录
        """
        if storage_dir is None:
            storage_dir = os.path.join(PROJECT_ROOT, "data")
            
        self.storage = DocumentStorage(storage_dir=storage_dir)
        self.uploader = FileUploader(upload_dir=storage_dir)
        self.ra = RetrievalAugmentation()
        logger.info(f"初始化文档管理器，存储目录: {storage_dir}")
    
    async def add_document(self, file_id: str) -> Optional[str]:
        """
        添加文档
        
        Args:
            file_id: 文件ID
            
        Returns:
            Optional[str]: 文档ID，添加失败则返回None
        """
        try:
            # 读取文件内容
            content = self.uploader.read_file_content(file_id)
            if not content:
                logger.error(f"读取文件内容失败: {file_id}")
                return None
            
            # 使用RetrievalAugmentation处理文档
            try:
                self.ra.add_documents(content)
                logger.info(f"文档处理成功: {file_id}")
            except Exception as e:
                logger.error(f"文档处理失败: {str(e)}")
                return None
            
            # 获取树结构
            tree_data = self.ra.get_all_nodes_info()
            
            # 保存文档和树结构
            if self.storage.save_document(file_id, content, tree_data):
                logger.info(f"文档添加成功: {file_id}")
                return file_id
            
            logger.error(f"保存文档失败: {file_id}")
            return None
        except Exception as e:
            logger.error(f"添加文档失败: {str(e)}")
            return None
    
    def get_document(self, doc_id: str) -> Optional[Dict]:
        """
        获取文档信息
        
        Args:
            doc_id: 文档ID
            
        Returns:
            Optional[Dict]: 文档信息，获取失败则返回None
        """
        try:
            return self.storage.get_document(doc_id)
        except Exception as e:
            logger.error(f"获取文档失败: {str(e)}")
            return None
    
    def delete_document(self, doc_id: str) -> bool:
        """
        删除文档
        
        Args:
            doc_id: 文档ID
            
        Returns:
            bool: 是否删除成功
        """
        try:
            return self.storage.delete_document(doc_id)
        except Exception as e:
            logger.error(f"删除文档失败: {str(e)}")
            return False
    
    def update_document_node(self, doc_id: str, node_id: str, new_text: str) -> bool:
        """
        更新文档节点内容
        
        Args:
            doc_id: 文档ID
            node_id: 节点ID
            new_text: 新的文本内容
            
        Returns:
            bool: 是否更新成功
        """
        try:
            # 获取文档信息
            doc_info = self.storage.get_document(doc_id)
            if not doc_info:
                return False
            
            # 更新树结构中的节点
            tree_data = doc_info["tree"]
            updated = False
            
            def update_node(nodes):
                nonlocal updated
                for node in nodes:
                    if node["id"] == node_id:
                        node["text"] = new_text
                        updated = True
                        return True
                    if "children" in node:
                        if update_node(node["children"]):
                            return True
                return False
            
            if "leaf_nodes" in tree_data:
                update_node(tree_data["leaf_nodes"])
            if "summary_nodes" in tree_data:
                for layer_nodes in tree_data["summary_nodes"].values():
                    update_node(layer_nodes)
            
            if not updated:
                return False
            
            # 保存更新后的树结构
            return self.storage.save_document(doc_id, doc_info["content"], tree_data)
        except Exception as e:
            logger.error(f"更新文档节点失败: {str(e)}")
            return False
    
    def list_documents(self) -> List[Dict]:
        """
        列出所有文档
        
        Returns:
            List[Dict]: 文档列表
        """
        try:
            return self.storage.list_documents()
        except Exception as e:
            logger.error(f"列出文档失败: {str(e)}")
            return []
