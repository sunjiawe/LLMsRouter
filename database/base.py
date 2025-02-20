from abc import ABC, abstractmethod
from typing import List, Optional
from models.user import User

class DatabaseProvider(ABC):
    @abstractmethod
    async def initialize(self) -> None:
        """初始化数据库连接和表结构"""
        pass
    
    @abstractmethod
    async def create_user(self, user: User) -> User:
        """创建新用户"""
        pass
    
    @abstractmethod
    async def get_user_by_username(self, username: str) -> Optional[User]:
        """通过用户名查找用户"""
        pass
    
    @abstractmethod
    async def get_user_by_api_key(self, api_key: str) -> Optional[User]:
        """通过API密钥查找用户"""
        pass
    
    @abstractmethod
    async def delete_user(self, username: str) -> bool:
        """删除用户"""
        pass
    
    @abstractmethod
    async def list_users(self) -> List[User]:
        """列出所有用户"""
        pass 