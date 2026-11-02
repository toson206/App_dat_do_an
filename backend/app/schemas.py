from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, Field

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
    cloned_from_session_id: Optional[int] = None
    menu_items: List[MenuItemCreate] = []

class SessionResponse(BaseModel):
    id: int
    share_code: str
    title: Optional[str]
    restaurant_id: Optional[int]
    created_by: str
    session_date: str
    deadline: datetime
    status: str
    event_note: Optional[str]
    bank_name: Optional[str]
    bank_account_number: Optional[str]
    bank_account_name: Optional[str]
    qr_image_url: Optional[str]
    shop_message: Optional[str]
    created_at: Optional[datetime]

# ----------------- ORDER SCHEMAS -----------------
class OrderItemCreate(BaseModel):
    menu_item_id: int
    quantity: int = Field(default=1, ge=1)
    item_note: Optional[str] = None

class OrderCreate(BaseModel):
    session_id: int
    user_id: str                      # UUID người ăn
    portion_custom_name: Optional[str] = None # Vd: "Phần 1", "Đặt hộ Lan"
    order_note: Optional[str] = None  # Ghi chú cả phần: "ít cơm", "không ớt"
    items: List[OrderItemCreate]

class OrderPriceUpdate(BaseModel):
    order_id: int
    final_price: float

class BatchPricingRequest(BaseModel):
    prices: List[OrderPriceUpdate]
    pricing_note: Optional[str] = None # Vd: "Đã gồm 5k ship mỗi phần"
