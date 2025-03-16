from typing import Dict, List, Optional, Any
from fastapi import Request, Response
from pydantic import BaseModel
import json
import asyncio
from loguru import logger

from .models import User
from .database import DatabaseProvider

# 用户 bypass 缓存
user_bypass_cache: Dict[str, str] = {}  # {username: model_name}

class BypassRequest(BaseModel):
    model: str

class BypassResponse(BaseModel):
    username: str
    bypass: str
    status: str
    message: str

async def set_user_bypass(
    request: Request, 
    bypass_request: BypassRequest, 
    db: DatabaseProvider,
    get_current_user,
    fetch_models_from_server,
    models_cache,
    config
):
    """设置用户的 bypass 模型"""
    # 用户认证
    current_user = await get_current_user(request, db)
    if not current_user:
        return Response(
            content=json.dumps({
                "status": "error",
                "message": "未授权"
            }),
            media_type="application/json",
            status_code=401
        )
    
    model = bypass_request.model
    
    # 如果模型是 "auto"，则清除 bypass 设置
    if model == "auto":
        if current_user.username in user_bypass_cache:
            del user_bypass_cache[current_user.username]
        return Response(
            content=json.dumps({
                "username": current_user.username,
                "bypass": "auto",
                "status": "success",
                "message": "已清除 bypass 设置"
            }),
            media_type="application/json"
        )
    
    # 验证模型是否在可用模型列表中
    available_models = []
    
    if models_cache:
        available_models = [m["id"] for m in models_cache.data]
    else:
        # 如果缓存不存在，则获取模型列表
        tasks = []
        for server_alias, server_config in config.servers.items():
            task = fetch_models_from_server(server_alias, server_config)
            tasks.append(task)
        
        models_lists = await asyncio.gather(*tasks)
        
        for models in models_lists:
            available_models.extend([m["id"] for m in models])
    
    if model not in available_models:
        return Response(
            content=json.dumps({
                "status": "error",
                "message": f"模型 {model} 不可用"
            }),
            media_type="application/json",
            status_code=400
        )
    
    # 设置 bypass
    user_bypass_cache[current_user.username] = model
    
    return Response(
        content=json.dumps({
            "username": current_user.username,
            "bypass": model,
            "status": "success",
            "message": f"已设置 bypass 为 {model}"
        }),
        media_type="application/json"
    )

async def get_user_bypass(request: Request, db: DatabaseProvider, get_current_user):
    """获取用户的 bypass 设置"""
    # 用户认证
    current_user = await get_current_user(request, db)
    if not current_user:
        return Response(
            content=json.dumps({
                "status": "error",
                "message": "未授权"
            }),
            media_type="application/json",
            status_code=401
        )
    
    # 获取 bypass 设置
    bypass = user_bypass_cache.get(current_user.username, "auto")
    
    return Response(
        content=json.dumps({
            "username": current_user.username,
            "bypass": bypass,
            "status": "success",
            "message": f"当前 bypass 设置为 {bypass}"
        }),
        media_type="application/json"
    )

def get_user_bypass_model(username: str) -> Optional[str]:
    """获取用户的 bypass 模型"""
    return user_bypass_cache.get(username) 