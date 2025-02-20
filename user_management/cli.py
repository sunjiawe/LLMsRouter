import asyncio
import argparse
import csv
import json
from typing import List, Optional
from .models import User
from .database import SQLiteProvider
from .auth import generate_api_key
from datetime import datetime

async def create_user(
    db: SQLiteProvider,
    username: str,
    email: Optional[str] = None
) -> User:
    """创建单个用户"""
    # 检查用户是否已存在
    existing_user = await db.get_user_by_username(username)
    if existing_user:
        raise ValueError(f"用户 '{username}' 已存在")
    
    # 创建新用户
    user = User(
        username=username,
        api_key=generate_api_key(),
        email=email
    )
    return await db.create_user(user)

async def import_users_from_csv(db: SQLiteProvider, file_path: str) -> List[User]:
    """从CSV文件导入用户"""
    users = []
    with open(file_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                user = await create_user(
                    db,
                    username=row['username'],
                    email=row.get('email')
                )
                users.append(user)
            except ValueError as e:
                print(f"警告: {str(e)}")
    return users

async def import_users_from_json(db: SQLiteProvider, file_path: str) -> List[User]:
    """从JSON文件导入用户"""
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
        users = []
        for item in data:
            try:
                user = await create_user(
                    db,
                    username=item['username'],
                    email=item.get('email')
                )
                users.append(user)
            except ValueError as e:
                print(f"警告: {str(e)}")
        return users

async def main():
    parser = argparse.ArgumentParser(description='用户管理工具')
    subparsers = parser.add_subparsers(dest='command', help='可用命令')
    
    # 添加用户
    add_parser = subparsers.add_parser('add', help='添加单个用户')
    add_parser.add_argument('username', help='用户名')
    add_parser.add_argument('--email', help='邮箱地址')
    
    # 删除用户
    delete_parser = subparsers.add_parser('delete', help='删除用户')
    delete_parser.add_argument('username', help='用户名')
    
    # 导入用户
    import_parser = subparsers.add_parser('import', help='从文件导入用户')
    import_parser.add_argument('file', help='CSV或JSON文件路径')
    
    # 列出用户
    subparsers.add_parser('list', help='列出所有用户')
    
    # 数据库路径
    parser.add_argument('--db', default='users.db', help='数据库文件路径')
    
    args = parser.parse_args()
    
    # 初始化数据库
    db = SQLiteProvider(args.db)
    await db.initialize()
    
    try:
        if args.command == 'add':
            user = await create_user(db, args.username, args.email)
            print(f"用户创建成功: {user.username} (API Key: {user.api_key})")
        
        elif args.command == 'delete':
            if await db.delete_user(args.username):
                print(f"用户 '{args.username}' 已删除")
            else:
                print(f"用户 '{args.username}' 不存在")
        
        elif args.command == 'import':
            if args.file.endswith('.csv'):
                users = await import_users_from_csv(db, args.file)
            elif args.file.endswith('.json'):
                users = await import_users_from_json(db, args.file)
            else:
                raise ValueError("不支持的文件格式，请使用.csv或.json文件")
            
            print(f"成功导入 {len(users)} 个用户")
            for user in users:
                print(f"- {user.username} (API Key: {user.api_key})")
        
        elif args.command == 'list':
            users = await db.list_users()
            print(f"共有 {len(users)} 个用户:")
            for user in users:
                print(f"- {user.username}")
                print(f"  API Key: {user.api_key}")
                if user.email:
                    print(f"  Email: {user.email}")
                print(f"  创建时间: {user.created_at}")
                print()
        
        else:
            parser.print_help()
    
    except Exception as e:
        print(f"错误: {str(e)}")

if __name__ == "__main__":
    asyncio.run(main()) 