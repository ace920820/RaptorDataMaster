"""
存储模块 - 负责文档树的存储和管理
"""
import json
import os
from typing import Dict, List, Optional
import logging
from datetime import datetime
from raptor import RetrievalAugmentation

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DocumentStorage:
    def __init__(self, storage_dir: str = "data/files", SAVE_PATH: str = "DATA/default_tree"):
        """
        初始化文档存储类
        
        Args:
            storage_dir: 文档存储目录
            SAVE_PATH: RA树结构保存路径
        """
        self.storage_dir = storage_dir
        self.metadata_file = os.path.join(storage_dir, "metadata.json")
        self._ensure_storage_exists()
        self.metadata = self._load_metadata()
        
        # 初始化RA
        self.SAVE_PATH = SAVE_PATH
        os.makedirs(os.path.dirname(SAVE_PATH), exist_ok=True)
        self.RA = RetrievalAugmentation(tree=self.SAVE_PATH)
        logger.info(f"初始化文档存储，存储目录: {storage_dir}, RA保存路径: {SAVE_PATH}")
    
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
    
    def save_document(self, doc_id: str, content: str, tree_data: Dict = None) -> bool:
        """
        保存文档内容和树结构
        
        Args:
            doc_id: 文档ID
            content: 文档内容
            tree_data: 树结构数据（已废弃，保留参数是为了兼容性）
            
        Returns:
            bool: 是否保存成功
        """
        try:
            # 保存文档内容
            doc_path = os.path.join(self.storage_dir, f"{doc_id}.txt")
            with open(doc_path, "w", encoding="utf-8") as f:
                f.write(content)
            
            # 更新RA树结构
            logger.info(f"将文档 {doc_id} 添加到RA树结构")
            self.RA.add_documents(content)
            self.RA.save(self.SAVE_PATH)
            
            # 更新元数据
            self.metadata[doc_id] = {
                "file_path": doc_path,
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
            
            # 获取树结构
            logger.info(f"从RA获取文档 {doc_id} 的树结构")
            tree_data = self.RA.get_all_nodes_info()
            
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
            
            # 从RA中删除文档节点
            logger.info(f"从RA树结构中删除文档 {doc_id}")
            # TODO: 实现从RA中删除文档的功能
            # 目前RA可能不支持删除单个文档，需要考虑如何实现这个功能
            # 可能需要重建整个树结构
            
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
