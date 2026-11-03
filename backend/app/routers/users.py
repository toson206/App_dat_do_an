from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session as DBSession
from app.database import get_db
from app.models import User

router = APIRouter(prefix="/api/users", tags=["Users (Quản lý nhân viên)"])

@router.get("/", summary="Lấy danh sách nhân viên")
def get_users(db: DBSession = Depends(get_db)):
    users = db.query(User).order_by(User.name).all()
    return [
        {
            "id": u.id,
            "name": u.name,
            "email": u.email,
            "department": u.department,
            "food_note": u.food_note,
            "favorite_food": u.favorite_food
        }
        for u in users
    ]

@router.get("/{user_id}", summary="Lấy thông tin 1 nhân viên")
def get_user(user_id: int, db: DBSession = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Không tìm thấy nhân viên!")
    return {
        "id": user.id,
        "name": user.name,
        "email": user.email,
        "department": user.department,
        "food_note": user.food_note,
        "favorite_food": user.favorite_food
    }

@router.post("/", summary="Tạo nhân viên mới (Đăng ký)")
def create_user(name: str, email: str, department: Optional[str] = None, db: DBSession = Depends(get_db)):
    # Kiểm tra email trùng
    existing = db.query(User).filter(User.email == email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email đã được sử dụng!")

    user = User(
        name=name,
        email=email,
        department=department
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    return {"message": "Tạo nhân viên thành công!", "user_id": user.id, "name": user.name}

@router.put("/{user_id}", summary="Cập nhật hồ sơ nhân viên")
def update_user(
    user_id: int,
    name: Optional[str] = None,
    department: Optional[str] = None,
    food_note: Optional[str] = None,
    favorite_food: Optional[str] = None,
    db: DBSession = Depends(get_db)
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Không tìm thấy nhân viên!")

    if name is not None:
        user.name = name
    if department is not None:
        user.department = department
    if food_note is not None:
        user.food_note = food_note
    if favorite_food is not None:
        user.favorite_food = favorite_food

    db.commit()
    return {"message": "Cập nhật hồ sơ thành công!"}
