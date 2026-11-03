from typing import List, Optional
from datetime import datetime, date
from decimal import Decimal
from pydantic import BaseModel, Field

# ----------------- USER SCHEMAS -----------------
class UserBase(BaseModel):
    name: str
    email: str
    department: Optional[str] = None
    favorite_food: Optional[str] = None

class UserCreate(UserBase):
    password: Optional[str] = None

class UserResponse(UserBase):
    id: int
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True

# ----------------- MENU ITEM SCHEMAS -----------------
class MenuItemBase(BaseModel):
    name: str
    image_url: Optional[str] = None
    price: Optional[float] = None
    display_order: int = 0

class MenuItemCreate(MenuItemBase):
    pass

class MenuItemResponse(MenuItemBase):
    id: int
    session_id: int
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True

# ----------------- ORDER ITEM SCHEMAS -----------------
class OrderItemCreate(BaseModel):
    menu_item_id: int
    quantity: int = Field(default=1, ge=1)
    item_note: Optional[str] = None

class OrderItemResponse(BaseModel):
    id: int
    menu_item_id: int
    quantity: int
    item_note: Optional[str] = None
    menu_item_name: Optional[str] = None

    class Config:
        from_attributes = True

# ----------------- ORDER SCHEMAS -----------------
class OrderCreate(BaseModel):
    session_id: int
    user_id: Optional[int] = None                     # ID người nhận suất cơm
    portion_custom_name: Optional[str] = None         # Vd: "Phần 1", "Đặt hộ Lan"
    order_note: Optional[str] = None                  # Ghi chú cả phần: "ít cơm", "không ớt"
    items: List[OrderItemCreate]

class OrderResponse(BaseModel):
    id: int
    session_id: int
    user_id: Optional[int] = None
    user_name: Optional[str] = None
    department: Optional[str] = None
    created_by_user_id: Optional[int] = None
    portion_custom_name: Optional[str] = None
    order_note: Optional[str] = None
    final_price: Optional[float] = None
    payment_status: str
    transferred_at: Optional[datetime] = None
    confirmed_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    items: List[OrderItemResponse] = []

    class Config:
        from_attributes = True

class OrderPriceUpdate(BaseModel):
    order_id: int
    final_price: float

class BatchPricingRequest(BaseModel):
    prices: List[OrderPriceUpdate]
    pricing_note: Optional[str] = None  # Ghi chú tính tiền (Vd: "Đã bao gồm 5k ship")

# ----------------- SESSION SCHEMAS -----------------
class SessionCreate(BaseModel):
    title: Optional[str] = "Cơm trưa văn phòng"
    deadline: datetime
    event_note: Optional[str] = None
    bank_name: Optional[str] = None
    bank_account_number: Optional[str] = None
    bank_account_name: Optional[str] = None
    qr_image_url: Optional[str] = None
    restaurant_id: Optional[int] = None
    created_by: Optional[int] = None
    cloned_from_session_id: Optional[int] = None
    menu_items: List[MenuItemCreate] = []

class SessionResponse(BaseModel):
    id: int
    share_code: str
    title: Optional[str] = None
    restaurant_id: Optional[int] = None
    created_by: Optional[int] = None
    session_date: Optional[date] = None
    deadline: datetime
    status: str
    event_note: Optional[str] = None
    bank_name: Optional[str] = None
    bank_account_number: Optional[str] = None
    bank_account_name: Optional[str] = None
    qr_image_url: Optional[str] = None
    shop_message: Optional[str] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class SessionDetailResponse(BaseModel):
    session: SessionResponse
    menu_items: List[MenuItemResponse]
    orders: List[OrderResponse]
