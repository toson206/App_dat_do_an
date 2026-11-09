from typing import Optional
from datetime import datetime
from pydantic import BaseModel

class UserBase(BaseModel):
    name: str
    email: str
    department: Optional[str] = None
    food_note: Optional[str] = None
    favorite_food: Optional[str] = None
    bank_name: Optional[str] = None
    bank_account_number: Optional[str] = None
    bank_account_name: Optional[str] = None
    qr_image_url: Optional[str] = None

class UserCreate(UserBase):
    password: Optional[str] = None

class UserUpdate(BaseModel):
    name: Optional[str] = None
    department: Optional[str] = None
    food_note: Optional[str] = None
    favorite_food: Optional[str] = None
    bank_name: Optional[str] = None
    bank_account_number: Optional[str] = None
    bank_account_name: Optional[str] = None
    qr_image_url: Optional[str] = None

class UserBankInfoUpdate(BaseModel):
    bank_name: Optional[str] = None
    bank_account_number: Optional[str] = None
    bank_account_name: Optional[str] = None
    qr_image_url: Optional[str] = None

class UserResponse(UserBase):
    id: int
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True
