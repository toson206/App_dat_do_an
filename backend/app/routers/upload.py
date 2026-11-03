import os
import uuid
import shutil
from fastapi import APIRouter, UploadFile, File, HTTPException
from app.config import settings

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

@router.post("/menu-image", summary="Tải ảnh món ăn lên (dùng khi tạo event)")
async def upload_menu_image(file: UploadFile = File(...)):
    """
    Người tạo event chọn ảnh món ăn từ máy hoặc dán từ clipboard.
    Ảnh được lưu vào thư mục uploads/menu/ và trả về link để hiển thị.
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

    # Trả về URL truy cập ảnh
    image_url = f"{settings.BASE_URL}/uploads/menu/{unique_name}"

    return {
        "message": "Tải ảnh thành công!",
        "image_url": image_url,
        "filename": unique_name
    }

@router.post("/qr-image", summary="Tải ảnh mã QR chuyển khoản lên")
async def upload_qr_image(file: UploadFile = File(...)):
    """
    Người tạo event tải ảnh mã QR ngân hàng để đồng nghiệp quét chuyển khoản.
    """
    validate_image(file)

    qr_dir = os.path.join(settings.UPLOAD_DIR, "qr")
    os.makedirs(qr_dir, exist_ok=True)

    ext = os.path.splitext(file.filename)[1].lower() if file.filename else ".jpg"
    unique_name = f"qr-{uuid.uuid4().hex}{ext}"
    file_path = os.path.join(qr_dir, unique_name)

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    image_url = f"{settings.BASE_URL}/uploads/qr/{unique_name}"

    return {
        "message": "Tải ảnh QR thành công!",
        "image_url": image_url,
        "filename": unique_name
    }
