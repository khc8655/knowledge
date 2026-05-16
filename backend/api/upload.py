"""
上传 API
"""
from fastapi import APIRouter, UploadFile, File, HTTPException
from typing import Optional
import hashlib
import shutil
from pathlib import Path
from datetime import datetime

router = APIRouter(tags=["upload"])

DATA_DIR = Path("./data")
UPLOAD_DIR = DATA_DIR / "uploads"

@router.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    force_overwrite: bool = False
):
    """上传文档"""
    # 检查文件类型
    allowed_extensions = {".docx", ".xlsx", ".txt", ".md", ".pptx"}
    ext = Path(file.filename).suffix.lower()
    if ext not in allowed_extensions:
        raise HTTPException(400, detail=f"不支持的文件类型: {ext}")
    
    # 读取文件内容
    content = await file.read()
    if len(content) == 0:
        raise HTTPException(400, detail="空文件")
    if len(content) > 50 * 1024 * 1024:  # 50MB
        raise HTTPException(400, detail="文件过大")
    
    # 计算 SHA256
    sha256 = hashlib.sha256(content).hexdigest()
    
    # 存储文件
    today = datetime.now().strftime("%Y-%m-%d")
    stored_name = f"{sha256[:8]}_{file.filename}"
    storage_path = UPLOAD_DIR / today / stored_name
    storage_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(storage_path, "wb") as f:
        f.write(content)
    
    # 创建 Job（后续实现）
    
    return {
        "status": "success",
        "filename": file.filename,
        "stored_name": stored_name,
        "sha256": sha256,
        "size_bytes": len(content)
    }

@router.get("/upload/documents")
async def list_documents(
    page: int = 1,
    page_size: int = 20,
    file_type: Optional[str] = None,
    is_current: Optional[bool] = None
):
    """列出已上传文档"""
    # TODO: 从数据库查询
    return {"documents": [], "total": 0, "page": page}

@router.delete("/upload/documents/{id}")
async def delete_document(id: int):
    """删除文档"""
    # TODO: 实现删除
    return {"status": "deleted", "id": id}

@router.post("/upload/documents/{id}/reprocess")
async def reprocess_document(id: int):
    """重新处理文档"""
    # TODO: 创建重新处理 Job
    return {"status": "job_created", "document_id": id}
