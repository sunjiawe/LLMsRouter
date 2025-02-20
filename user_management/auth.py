import secrets
import string
from typing import Optional
from fastapi import Request, HTTPException
from .models import User
from .database import DatabaseProvider

def generate_api_key(length: int = 32) -> str:
    """生成随机API密钥"""
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))

async def get_current_user(
    request: Request,
    db: DatabaseProvider,
    require_auth: bool = True
) -> Optional[User]:
    """从请求中获取当前用户"""
    auth_header = request.headers.get("authorization", "")
    if not auth_header.startswith("Bearer "):
        if require_auth:
            raise HTTPException(
                status_code=401,
                detail="Missing or invalid authentication token"
            )
        return None
    
    api_key = auth_header.replace("Bearer ", "")
    user = await db.get_user_by_api_key(api_key)
    
    if require_auth and not user:
        raise HTTPException(
            status_code=401,
            detail="Invalid authentication token"
        )
    
    return user 