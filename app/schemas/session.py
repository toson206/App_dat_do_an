from typing import List, Optional
from datetime import datetime, date
from pydantic import BaseModel
from app.schemas.menu_item import MenuItemCreate, MenuItemResponse
from app.schemas.order import OrderResponse

class SessionCloneRequest(BaseModel):
    deadline: datetime
    title: Optional[str] = None
    event_note: Optional[str] = None
    include_menu: bool = True

class SessionCreate(BaseModel):
    title: Optional[str] = "Cơm trưa văn phòng"
    deadline: datetime
    event_note: Optional[str] = None
    pricing_note: Optional[str] = None
    bank_name: Optional[str] = None
    bank_account_number: Optional[str] = None
    bank_account_name: Optional[str] = None
    qr_image_url: Optional[str] = None
    restaurant_id: Optional[int] = None
    created_by: Optional[int] = None
    cloned_from_session_id: Optional[int] = None
    menu_items: List[MenuItemCreate] = []

class SessionUpdate(BaseModel):
    title: Optional[str] = None
    deadline: Optional[datetime] = None
    event_note: Optional[str] = None
    pricing_note: Optional[str] = None
    bank_name: Optional[str] = None
    bank_account_number: Optional[str] = None
    bank_account_name: Optional[str] = None
    qr_image_url: Optional[str] = None
    restaurant_id: Optional[int] = None

class SessionResponse(BaseModel):
    id: int
    share_code: str
    title: Optional[str] = None
    restaurant_id: Optional[int] = None
    created_by: Optional[int] = None
    cloned_from_session_id: Optional[int] = None
    cloned_from_title: Optional[str] = None
    session_date: Optional[date] = None
    deadline: datetime
    status: str
    event_note: Optional[str] = None
    pricing_note: Optional[str] = None
    bank_name: Optional[str] = None
    bank_account_number: Optional[str] = None
    bank_account_name: Optional[str] = None
    qr_image_url: Optional[str] = None
    shop_message: Optional[str] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class SessionCandidateResponse(BaseModel):
    id: int
    share_code: str
    title: Optional[str] = None
    restaurant_id: Optional[int] = None
    restaurant_name: Optional[str] = None
    created_by: Optional[int] = None
    creator_name: Optional[str] = None
    session_date: Optional[date] = None
    menu_items_count: int = 0
    total_orders_count: int = 0
    status: str
    created_at: Optional[datetime] = None

class SessionDetailResponse(BaseModel):
    session: SessionResponse
    menu_items: List[MenuItemResponse]
    orders: List[OrderResponse]
