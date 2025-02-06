"""
API模块 - 提供REST API接口
"""
import os
from fastapi import FastAPI, File, UploadFile, HTTPException
from typing import List, Dict, Optional
import logging
from .manage import DocumentManager
from .upload import FileUploader

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="文档管理API",
    description="基于FastAPI的文档管理系统",
    version="1.0.0"
)

# 确定存储目录
if os.environ.get("TESTING") == "1":
    # 测试环境使用测试数据目录
    storage_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "tests", "test_data")
else:
    # 生产环境使用正式数据目录
    storage_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")

# 初始化管理器
document_manager = DocumentManager(storage_dir=storage_dir)
file_uploader = FileUploader(upload_dir=storage_dir)

@app.post("/documents/upload", response_model=Dict[str, str])
async def upload_document(file: UploadFile = File(...)):
    """
    上传文档
    
    Args:
        file: 上传的文件
        
    Returns:
        Dict[str, str]: 包含文档ID的响应
    """
    try:
        # 保存上传的文件
        file_id = await file_uploader.save_upload_file(file)
        if not file_id:
            logger.error("文件上传失败")
            raise HTTPException(status_code=400, detail="文件上传失败")
        
        # 添加文档
        doc_id = await document_manager.add_document(file_id)
        if not doc_id:
            logger.error("文档处理失败")
            raise HTTPException(status_code=500, detail="文档处理失败")
        
        logger.info(f"文档上传成功: {doc_id}")
        return {"document_id": doc_id}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"文档上传失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/documents", response_model=List[Dict])
async def list_documents():
    """
    列出所有文档
    
    Returns:
        List[Dict]: 文档列表
    """
    try:
        documents = document_manager.list_documents()
        return documents
    except Exception as e:
        logger.error(f"获取文档列表失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/documents/{doc_id}", response_model=Dict)
async def get_document(doc_id: str):
    """
    获取文档信息
    
    Args:
        doc_id: 文档ID
        
    Returns:
        Dict: 文档信息
    """
    try:
        doc_info = document_manager.get_document(doc_id)
        if not doc_info:
            logger.warning(f"文档不存在: {doc_id}")
            raise HTTPException(status_code=404, detail="文档不存在")
        return doc_info
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取文档失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/documents/{doc_id}", response_model=Dict[str, str])
async def delete_document(doc_id: str):
    """
    删除文档
    
    Args:
        doc_id: 文档ID
        
    Returns:
        Dict[str, str]: 操作结果
    """
    try:
        if document_manager.delete_document(doc_id):
            logger.info(f"文档删除成功: {doc_id}")
            return {"message": "删除成功"}
            
        logger.warning(f"文档不存在: {doc_id}")
        raise HTTPException(status_code=404, detail="文档不存在")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除文档失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.patch("/documents/{doc_id}/nodes/{node_id}", response_model=Dict[str, str])
async def update_document_node(doc_id: str, node_id: str, new_text: str):
    """
    更新文档节点内容
    
    Args:
        doc_id: 文档ID
        node_id: 节点ID
        new_text: 新的文本内容
        
    Returns:
        Dict[str, str]: 操作结果
    """
    try:
        if document_manager.update_document_node(doc_id, node_id, new_text):
            logger.info(f"文档节点更新成功: {doc_id}/{node_id}")
            return {"message": "更新成功"}
            
        logger.warning(f"文档或节点不存在: {doc_id}/{node_id}")
        raise HTTPException(status_code=404, detail="文档或节点不存在")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新文档节点失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
