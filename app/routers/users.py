from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session as DBSession
from app.database import get_db
from app.models import User
from app.schemas.user import UserCreate, UserUpdate, UserBankInfoUpdate, UserResponse

router = APIRouter(prefix="/api/users", tags=["Users (Quản lý nhân viên)"])

@router.get("/", response_model=List[UserResponse], summary="Lấy danh sách nhân viên")
def get_users(db: DBSession = Depends(get_db)):
    users = db.query(User).order_by(User.name).all()
    return users

@router.get("/{user_id}", response_model=UserResponse, summary="Lấy thông tin 1 nhân viên")
def get_user(user_id: int, db: DBSession = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Không tìm thấy nhân viên!")
    return user

@router.post("/", summary="Tạo nhân viên mới (Đăng ký)")
def create_user(data: UserCreate, db: DBSession = Depends(get_db)):
    # Kiểm tra email trùng
    existing = db.query(User).filter(User.email == data.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email đã được sử dụng!")

    user = User(
        name=data.name,
        email=data.email,
        department=data.department,
        food_note=data.food_note,
        favorite_food=data.favorite_food,
        bank_name=data.bank_name,
        bank_account_number=data.bank_account_number,
        bank_account_name=data.bank_account_name,
        qr_image_url=data.qr_image_url
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    return {"message": "Tạo nhân viên thành công!", "user_id": user.id, "name": user.name}

@router.put("/{user_id}", summary="Cập nhật hồ sơ nhân viên")
def update_user(user_id: int, data: UserUpdate, db: DBSession = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Không tìm thấy nhân viên!")

    if data.name is not None:
        user.name = data.name
    if data.department is not None:
        user.department = data.department
    if data.food_note is not None:
        user.food_note = data.food_note
    if data.favorite_food is not None:
        user.favorite_food = data.favorite_food
    if data.bank_name is not None:
        user.bank_name = data.bank_name
    if data.bank_account_number is not None:
        user.bank_account_number = data.bank_account_number
    if data.bank_account_name is not None:
        user.bank_account_name = data.bank_account_name
    if data.qr_image_url is not None:
        user.qr_image_url = data.qr_image_url

    db.commit()
    db.refresh(user)
    return {"message": "Cập nhật hồ sơ thành công!", "user": user}

@router.put("/{user_id}/bank-info", summary="Cập nhật tài khoản ngân hàng và mã QR cá nhân")
def update_bank_info(user_id: int, data: UserBankInfoUpdate, db: DBSession = Depends(get_db)):
    """
    Nhân viên cài đặt thông tin STK và mã QR nhận tiền một lần duy nhất.
    Khi người này tạo event đặt cơm, hệ thống sẽ tự động lấy thông tin này.
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Không tìm thấy nhân viên!")

    if data.bank_name is not None:
        user.bank_name = data.bank_name
    if data.bank_account_number is not None:
        user.bank_account_number = data.bank_account_number
    if data.bank_account_name is not None:
        user.bank_account_name = data.bank_account_name
    if data.qr_image_url is not None:
        user.qr_image_url = data.qr_image_url

    db.commit()
    db.refresh(user)
    return {
        "message": "Cập nhật thông tin ngân hàng & QR thành công!",
        "bank_name": user.bank_name,
        "bank_account_number": user.bank_account_number,
        "bank_account_name": user.bank_account_name,
        "qr_image_url": user.qr_image_url
    }
