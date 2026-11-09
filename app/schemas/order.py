from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, Field

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

class OrderCreate(BaseModel):
    session_id: int
    user_id: Optional[int] = None                     # ID người nhận suất cơm
    portion_custom_name: Optional[str] = None         # Vd: "Phần 1", "Đặt hộ Lan"
    order_note: Optional[str] = None                  # Ghi chú cả phần: "ít cơm", "không ớt"
    items: List[OrderItemCreate]

class OrderUpdate(BaseModel):
    user_id: Optional[int] = None                     # ID người nhận suất cơm (nếu đổi người ăn hộ)
    portion_custom_name: Optional[str] = None         # Vd: "Phần 1", "Đặt hộ Lan"
    order_note: Optional[str] = None                  # Ghi chú: "ít cơm", "không cay"
    items: Optional[List[OrderItemCreate]] = None     # Danh sách món cập nhật mới (nếu có)

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
