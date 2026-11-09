from typing import Optional
from datetime import datetime
from pydantic import BaseModel

class MenuItemBase(BaseModel):
    name: str
    image_url: Optional[str] = None
    price: Optional[float] = None
    display_order: int = 0

class MenuItemCreate(MenuItemBase):
    pass

class MenuItemUpdate(BaseModel):
    name: Optional[str] = None
    image_url: Optional[str] = None
    price: Optional[float] = None
    display_order: Optional[int] = None

class MenuItemResponse(MenuItemBase):
    id: int
    session_id: int
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True
