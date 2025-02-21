from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime

class User(BaseModel):
    username: str
    api_key: str
    email: Optional[EmailStr] = None
    created_at: datetime = datetime.now()
    updated_at: datetime = datetime.now()
    permissions: Optional[dict] = {}  # 用户对不同provider的访问权限

    class Config:
        from_attributes = True 