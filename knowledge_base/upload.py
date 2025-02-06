"""
上传模块 - 处理文件上传和读取
"""
import os
import uuid
import logging
from typing import Optional
from fastapi import UploadFile

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class FileUploader:
    """文件上传处理类
    
    负责处理文件的上传、保存和读取操作
    """
    
    def __init__(self, upload_dir: Optional[str] = None):
        """初始化上传处理器
        
        Args:
            upload_dir: 上传文件存储目录，如果不指定则使用默认目录
        """
        if upload_dir is None:
            # 默认使用项目根目录下的uploads目录
            upload_dir = os.path.join(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                "uploads"
            )
        
        self.upload_dir = upload_dir
        os.makedirs(upload_dir, exist_ok=True)
        logger.info(f"初始化文件上传处理器，上传目录: {upload_dir}")
    
    async def save_upload_file(self, file: UploadFile) -> Optional[str]:
        """保存上传的文件
        
        Args:
            file: 上传的文件对象
            
        Returns:
            Optional[str]: 文件ID，保存失败则返回None
        """
        try:
            # 生成唯一的文件ID
            file_id = str(uuid.uuid4())
            
            # 读取文件内容
            content = await file.read()
            
            # 保存文件
            file_path = os.path.join(self.upload_dir, f"{file_id}.txt")
            with open(file_path, "wb") as f:
                f.write(content)
            
            logger.info(f"文件上传成功: {file_id}")
            return file_id
            
        except Exception as e:
            logger.error(f"文件上传失败: {str(e)}")
            return None
    
    def read_file_content(self, file_id: str) -> Optional[str]:
        """读取文件内容
        
        Args:
            file_id: 文件ID
            
        Returns:
            Optional[str]: 文件内容，读取失败则返回None
        """
        try:
            file_path = os.path.join(self.upload_dir, f"{file_id}.txt")
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            
            logger.info(f"读取文件成功: {file_id}")
            return content
            
        except Exception as e:
            logger.error(f"读取文件失败: {str(e)}")
            return None
