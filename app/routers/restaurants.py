from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session as DBSession
from app.database import get_db
from app.models import Restaurant, Session
from app.schemas.restaurant import RestaurantCreate, RestaurantUpdate, RestaurantResponse

router = APIRouter(prefix="/api/restaurants", tags=["Restaurants (Quán ăn)"])

@router.get("/", response_model=List[RestaurantResponse], summary="Lấy danh sách các quán ăn")
def get_restaurants(
    q: Optional[str] = Query(None, description="Tìm kiếm theo tên quán hoặc địa chỉ"),
    limit: int = Query(50, ge=1, le=100),
    db: DBSession = Depends(get_db)
):
    """
    Lấy danh sách các quán ăn đã lưu trong hệ thống để Host chọn nhanh khi tạo event
    """
    query = db.query(Restaurant)
    if q:
        search_pattern = f"%{q}%"
        query = query.filter(
            (Restaurant.name.ilike(search_pattern)) | 
            (Restaurant.address.ilike(search_pattern))
        )
    restaurants = query.order_by(Restaurant.id.desc()).limit(limit).all()
    return restaurants

@router.get("/{restaurant_id}", response_model=RestaurantResponse, summary="Lấy chi tiết 1 quán ăn")
def get_restaurant(restaurant_id: int, db: DBSession = Depends(get_db)):
    """
    Xem thông tin chi tiết một quán ăn
    """
    restaurant = db.query(Restaurant).filter(Restaurant.id == restaurant_id).first()
    if not restaurant:
        raise HTTPException(status_code=404, detail="Không tìm thấy quán ăn này!")
    return restaurant

@router.post("/", response_model=RestaurantResponse, summary="Thêm quán ăn mới")
def create_restaurant(data: RestaurantCreate, db: DBSession = Depends(get_db)):
    """
    Thêm một quán cơm/quán nước mới vào danh sách quán quen
    """
    # Kiểm tra trùng tên quán
    existing = db.query(Restaurant).filter(Restaurant.name.ilike(data.name.strip())).first()
    if existing:
        raise HTTPException(status_code=400, detail=f"Quán '{data.name}' đã tồn tại trong hệ thống!")

    restaurant = Restaurant(
        name=data.name.strip(),
        phone=data.phone.strip() if data.phone else None,
        address=data.address.strip() if data.address else None,
        menu_url=data.menu_url.strip() if data.menu_url else None
    )
    db.add(restaurant)
    db.commit()
    db.refresh(restaurant)
    return restaurant

@router.put("/{restaurant_id}", response_model=RestaurantResponse, summary="Cập nhật thông tin quán ăn")
def update_restaurant(
    restaurant_id: int, 
    data: RestaurantUpdate, 
    db: DBSession = Depends(get_db)
):
    """
    Cập nhật tên, số điện thoại, địa chỉ hoặc link menu của quán
    """
    restaurant = db.query(Restaurant).filter(Restaurant.id == restaurant_id).first()
    if not restaurant:
        raise HTTPException(status_code=404, detail="Không tìm thấy quán ăn!")

    if data.name is not None:
        name_clean = data.name.strip()
        # Kiểm tra trùng tên nếu đổi sang tên khác
        conflict = db.query(Restaurant).filter(
            Restaurant.name.ilike(name_clean),
            Restaurant.id != restaurant_id
        ).first()
        if conflict:
            raise HTTPException(status_code=400, detail=f"Tên quán '{name_clean}' đã được sử dụng!")
        restaurant.name = name_clean

    if data.phone is not None:
        restaurant.phone = data.phone.strip() if data.phone else None
    if data.address is not None:
        restaurant.address = data.address.strip() if data.address else None
    if data.menu_url is not None:
        restaurant.menu_url = data.menu_url.strip() if data.menu_url else None

    db.commit()
    db.refresh(restaurant)
    return restaurant

@router.delete("/{restaurant_id}", summary="Xóa quán ăn")
def delete_restaurant(restaurant_id: int, db: DBSession = Depends(get_db)):
    """
    Xóa quán ăn khỏi hệ thống:
    - Nếu quán đã từng được liên kết với các event đặt cơm trước đó, hệ thống sẽ gỡ liên kết (SET NULL) để không làm mất lịch sử các event cũ.
    """
    restaurant = db.query(Restaurant).filter(Restaurant.id == restaurant_id).first()
    if not restaurant:
        raise HTTPException(status_code=404, detail="Không tìm thấy quán ăn!")

    # Set restaurant_id = NULL cho các session cũ để bảo toàn dữ liệu lịch sử
    db.query(Session).filter(Session.restaurant_id == restaurant_id).update({Session.restaurant_id: None})
    
    db.delete(restaurant)
    db.commit()
    return {"message": f"Đã xóa quán '{restaurant.name}' thành công!"}
