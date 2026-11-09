from typing import Optional
from datetime import datetime
from pydantic import BaseModel

class RestaurantBase(BaseModel):
    name: str
    phone: Optional[str] = None
    address: Optional[str] = None
    menu_url: Optional[str] = None

class RestaurantCreate(RestaurantBase):
    pass

class RestaurantUpdate(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    menu_url: Optional[str] = None

class RestaurantResponse(RestaurantBase):
    id: int
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True
