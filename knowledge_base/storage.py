"""
存储模块 - 负责文档树的存储和管理
"""
import json
import os
from typing import Dict, List, Optional
import logging
from datetime import datetime

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DocumentStorage:
    def __init__(self, storage_dir: str = "data/files"):
        """
        初始化文档存储类
        
        Args:
            storage_dir: 文档存储目录
        """
        self.storage_dir = storage_dir
        self.metadata_file = os.path.join(storage_dir, "metadata.json")
        self._ensure_storage_exists()
        self.metadata = self._load_metadata()
        
        logger.info(f"初始化文档存储，存储目录: {storage_dir}")
    
    def _ensure_storage_exists(self):
        """确保存储目录和元数据文件存在"""
        os.makedirs(self.storage_dir, exist_ok=True)
        if not os.path.exists(self.metadata_file):
            with open(self.metadata_file, "w", encoding="utf-8") as f:
                json.dump({}, f, ensure_ascii=False, indent=2)
    
    def _load_metadata(self) -> Dict:
        """加载元数据"""
        try:
            with open(self.metadata_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"加载元数据失败: {str(e)}")
            return {}
    
    def _save_metadata(self):
        """保存元数据"""
        try:
            with open(self.metadata_file, "w", encoding="utf-8") as f:
                json.dump(self.metadata, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"保存元数据失败: {str(e)}")
    
    def save_document(self, doc_id: str, content: str, tree_data: Dict) -> bool:
        """
        保存文档内容和树结构
        
        Args:
            doc_id: 文档ID
            content: 文档内容
            tree_data: 树结构数据
            
        Returns:
            bool: 是否保存成功
        """
        try:
            # 保存文档内容
            doc_path = os.path.join(self.storage_dir, f"{doc_id}.txt")
            with open(doc_path, "w", encoding="utf-8") as f:
                f.write(content)
            
            # 保存树结构
            tree_path = os.path.join(self.storage_dir, f"{doc_id}_tree.json")
            with open(tree_path, "w", encoding="utf-8") as f:
                json.dump(tree_data, f, ensure_ascii=False, indent=2)
            
            # 更新元数据
            self.metadata[doc_id] = {
                "file_path": doc_path,
                "tree_path": tree_path,
                "created_at": datetime.now().isoformat()
            }
            self._save_metadata()
            
            logger.info(f"文档 {doc_id} 保存成功")
            return True
        except Exception as e:
            logger.error(f"保存文档 {doc_id} 失败: {str(e)}")
            return False
    
    def get_document(self, doc_id: str) -> Optional[Dict]:
        """
        获取文档内容和树结构
        
        Args:
            doc_id: 文档ID
            
        Returns:
            Optional[Dict]: 文档数据，包含content和tree字段
        """
        try:
            if doc_id not in self.metadata:
                return None
            
            doc_info = self.metadata[doc_id]
            
            # 读取文档内容
            with open(doc_info["file_path"], "r", encoding="utf-8") as f:
                content = f.read()
            
            # 读取树结构
            with open(doc_info["tree_path"], "r", encoding="utf-8") as f:
                tree_data = json.load(f)
            
            return {
                "id": doc_id,
                "content": content,
                "tree": tree_data,
                "created_at": doc_info["created_at"]
            }
        except Exception as e:
            logger.error(f"获取文档 {doc_id} 失败: {str(e)}")
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
            if doc_id not in self.metadata:
                return False
            
            doc_info = self.metadata[doc_id]
            
            # 删除文件
            os.remove(doc_info["file_path"])
            os.remove(doc_info["tree_path"])
            
            # 更新元数据
            del self.metadata[doc_id]
            self._save_metadata()
            
            logger.info(f"文档 {doc_id} 删除成功")
            return True
        except Exception as e:
            logger.error(f"删除文档 {doc_id} 失败: {str(e)}")
            return False
    
    def list_documents(self) -> List[Dict]:
        """
        列出所有文档
        
        Returns:
            List[Dict]: 文档列表
        """
        try:
            documents = []
            for doc_id, info in self.metadata.items():
                documents.append({
                    "id": doc_id,
                    "created_at": info["created_at"]
                })
            return documents
        except Exception as e:
            logger.error(f"列出文档失败: {str(e)}")
            return []
