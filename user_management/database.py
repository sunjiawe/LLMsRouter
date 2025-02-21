from abc import ABC, abstractmethod
from typing import List, Optional
import aiosqlite
from datetime import datetime
from .models import User
import json

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

class SQLiteProvider(DatabaseProvider):
    def __init__(self, db_path: str = "users.db"):
        self.db_path = db_path
        
    async def initialize(self) -> None:
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    username TEXT PRIMARY KEY,
                    api_key TEXT UNIQUE NOT NULL,
                    email TEXT,
                    permissions TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """)
            await db.commit()
    
    async def create_user(self, user: User) -> User:
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """
                INSERT INTO users (username, api_key, email, permissions, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (user.username, user.api_key, user.email, json.dumps(user.permissions), 
                 user.created_at.isoformat(), user.updated_at.isoformat())
            )
            await db.commit()
            return user
    
    async def get_user_by_username(self, username: str) -> Optional[User]:
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(
                "SELECT * FROM users WHERE username = ?",
                (username,)
            ) as cursor:
                row = await cursor.fetchone()
                if row:
                    return self._row_to_user(row)
        return None
    
    async def get_user_by_api_key(self, api_key: str) -> Optional[User]:
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(
                "SELECT * FROM users WHERE api_key = ?",
                (api_key,)
            ) as cursor:
                row = await cursor.fetchone()
                if row:
                    return self._row_to_user(row)
        return None
    
    async def delete_user(self, username: str) -> bool:
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                "DELETE FROM users WHERE username = ?",
                (username,)
            )
            await db.commit()
            return cursor.rowcount > 0
    
    async def list_users(self) -> List[User]:
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("SELECT * FROM users") as cursor:
                rows = await cursor.fetchall()
                return [self._row_to_user(row) for row in rows]
    
    async def update_user_permissions(self, username: str, permissions: dict) -> bool:
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                """
                UPDATE users SET permissions = ? WHERE username = ?
                """,
                (json.dumps(permissions), username)
            )
            await db.commit()
            return cursor.rowcount > 0
    
    def _row_to_user(self, row) -> User:
        return User(
            username=row[0],
            api_key=row[1],
            email=row[2] if row[2] else None,
            permissions=json.loads(row[3]),
            created_at=datetime.fromisoformat(row[4]),
            updated_at=datetime.fromisoformat(row[5])
        ) 