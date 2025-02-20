import secrets
import string
from typing import Optional, Dict
from fastapi import Request, HTTPException
from .models import User
from .database import DatabaseProvider
import time
from threading import Lock

# 用户认证缓存
class UserAuthCache:
    def __init__(self, ttl_seconds: int = 3600):  # 默认缓存60分钟
        self.cache: Dict[str, tuple[User, float]] = {}  # {token: (user, timestamp)}
        self.ttl = ttl_seconds
        self.lock = Lock()
    
    def get(self, token: str) -> Optional[User]:
        """获取缓存的用户信息"""
        with self.lock:
            if token in self.cache:
                user, timestamp = self.cache[token]
                if time.time() - timestamp <= self.ttl:
                    return user
                # 过期则删除
                del self.cache[token]
        return None
    
    def set(self, token: str, user: User):
        """设置缓存"""
        with self.lock:
            self.cache[token] = (user, time.time())
    
    def invalidate(self, token: str):
        """使指定的缓存失效"""
        with self.lock:
            self.cache.pop(token, None)
    
    def clear(self):
        """清空所有缓存"""
        with self.lock:
            self.cache.clear()

# 全局缓存实例
auth_cache = UserAuthCache()

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
    
    token = auth_header.replace("Bearer ", "")
    
    # 先检查缓存
    user = auth_cache.get(token)
    if user:
        return user
    
    # 缓存未命中，查询数据库
    user = await db.get_user_by_api_key(token)
    
    if user:
        # 将结果加入缓存
        auth_cache.set(token, user)
    elif require_auth:
        raise HTTPException(
            status_code=401,
            detail="Invalid authentication token"
        )
    
    return user 