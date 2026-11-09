import os
import uuid
import shutil
from typing import Optional
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from sqlalchemy.orm import Session as DBSession
from app.config import settings
from app.database import get_db
from app.models import User
from app.dependencies import get_current_user_id

router = APIRouter(prefix="/api/upload", tags=["Upload (Tải ảnh lên)"])

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp"}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

def validate_image(file: UploadFile):
    """Kiểm tra file ảnh hợp lệ"""
    ext = os.path.splitext(file.filename)[1].lower() if file.filename else ""
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Chỉ cho phép các loại ảnh: {', '.join(ALLOWED_EXTENSIONS)}"
        )

@router.post("/menu-image", summary="Tải ảnh món ăn lên máy chủ")
async def upload_menu_image(file: UploadFile = File(...)):
    """
    Tải file ảnh món ăn lên máy chủ.
    Ảnh được lưu vào thư mục uploads/menu/ và trả về đường dẫn URL tương đối để lưu vào database.
    """
    validate_image(file)

    # Tạo thư mục nếu chưa có
    menu_dir = os.path.join(settings.UPLOAD_DIR, "menu")
    os.makedirs(menu_dir, exist_ok=True)

    # Đặt tên file duy nhất tránh trùng
    ext = os.path.splitext(file.filename)[1].lower() if file.filename else ".jpg"
    unique_name = f"{uuid.uuid4().hex}{ext}"
    file_path = os.path.join(menu_dir, unique_name)

    # Lưu file
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    relative_url = f"/uploads/menu/{unique_name}"
    full_url = f"{settings.BASE_URL}{relative_url}"

    return {
        "message": "Tải ảnh thành công!",
        "image_url": relative_url,
        "full_url": full_url,
        "filename": unique_name
    }

@router.post("/qr-image", summary="Tải ảnh mã QR chuyển khoản lên (Gắn trực tiếp vào User)")
async def upload_qr_image(
    file: UploadFile = File(...),
    save_to_user: bool = True,
    current_user_id: int = Depends(get_current_user_id),
    db: DBSession = Depends(get_db)
):
    """
    Tải ảnh mã QR ngân hàng lên:
    - Lưu file vào thư mục uploads/qr/
    - Tự động gắn link QR này vào hồ sơ cá nhân của nhân viên (User ID) nếu save_to_user = True
    """
    validate_image(file)

    qr_dir = os.path.join(settings.UPLOAD_DIR, "qr")
    os.makedirs(qr_dir, exist_ok=True)

    ext = os.path.splitext(file.filename)[1].lower() if file.filename else ".jpg"
    unique_name = f"qr-{uuid.uuid4().hex}{ext}"
    file_path = os.path.join(qr_dir, unique_name)

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    relative_url = f"/uploads/qr/{unique_name}"
    full_url = f"{settings.BASE_URL}{relative_url}"

    # Tự động gán mã QR vào User đang thao tác
    updated_user_id = None
    if save_to_user:
        user = db.query(User).filter(User.id == current_user_id).first()
        if user:
            user.qr_image_url = relative_url
            db.commit()
            updated_user_id = user.id

    return {
        "message": "Tải ảnh QR thành công!",
        "image_url": relative_url,
        "full_url": full_url,
        "filename": unique_name,
        "attached_to_user_id": updated_user_id
    }
