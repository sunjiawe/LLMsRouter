from fastapi import FastAPI, Request, Response
from fastapi.responses import StreamingResponse
from openai import OpenAI, AsyncOpenAI
from loguru import logger
import json
import yaml
from typing import Optional, Dict, Any, List
import os
from datetime import datetime
import asyncio
from pydantic import BaseModel

# 配置日志
logger.add("api_proxy.log", 
           format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}",
           rotation="500 MB")

class ServerConfig(BaseModel):
    url: str
    api_key: str

class Config(BaseModel):
    servers: Dict[str, ServerConfig]

# 全局配置
config: Config = None

def load_config(config_path: str = "config.yaml") -> Config:
    """加载YAML配置文件"""
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config_data = yaml.safe_load(f)
            return Config(**config_data)
    except Exception as e:
        logger.error(f"加载配置文件失败: {str(e)}")
        raise

app = FastAPI(title="OpenAI API Proxy Router")

@app.on_event("startup")
async def startup_event():
    """服务启动时加载配置"""
    global config
    config = load_config()
    logger.info(f"已加载服务器配置: {list(config.servers.keys())}")

async def log_request_response(request_data: Dict[Any, Any], 
                             response_data: Dict[Any, Any], 
                             target_url: str,
                             is_stream: bool):
    """记录请求和响应的详细信息"""
    model_name = request_data.get("model", "unknown")
    
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "model": model_name,
        "target_url": target_url,
        "is_stream": is_stream,
        "request": request_data,
    }
    
    if not is_stream:
        usage = response_data.get("usage", {})
        log_entry.update({
            "response": response_data,
            "tokens": {
                "prompt": usage.get("prompt_tokens", 0),
                "completion": usage.get("completion_tokens", 0),
                "total": usage.get("total_tokens", 0)
            }
        })
    
    logger.info(json.dumps(log_entry, ensure_ascii=False))

def get_server_config(server_alias: str) -> Optional[ServerConfig]:
    """根据服务器别名获取服务器配置"""
    return config.servers.get(server_alias)

def parse_target_url(model: str, proxy_url: Optional[str] = None) -> tuple[str, Optional[str]]:
    """解析目标URL和服务器别名
    支持两种模式：
    1. proxy模式：直接使用proxy_url参数
    2. auto模式：从model名称中解析，格式为[server_alias]model_name
    """
    if proxy_url:
        return proxy_url, None
    
    if model.startswith("[") and "]" in model:
        server_alias = model[1:model.index("]")]
        server_config = get_server_config(server_alias)
        if server_config:
            return server_config.url, server_alias
        raise ValueError(f"未找到服务器别名 '{server_alias}' 的配置")
    
    raise ValueError("无法确定目标服务器URL，请使用 [server_alias]model_name 格式或提供 proxy 参数")

def extract_real_model_name(model: str) -> str:
    """从model字段中提取真实的模型名称"""
    if model.startswith("[") and "]" in model:
        return model[model.index("]") + 1:]
    return model

def get_api_key(headers: Dict[str, str], server_alias: Optional[str]) -> str:
    """获取API密钥
    优先使用配置文件中的API密钥，如果没有则使用请求头中的API密钥
    """
    if server_alias and server_alias in config.servers:
        return config.servers[server_alias].api_key
    
    api_key = headers.get("authorization", "").replace("Bearer ", "")
    if api_key:
        return api_key
    
    raise ValueError("未找到有效的API密钥")

async def fetch_models_from_server(server_alias: str, server_config: ServerConfig) -> List[Dict[str, Any]]:
    """从单个服务器获取模型列表"""
    try:
        print(f"server_alias: {server_alias}, server_config: {server_config}")
        client = AsyncOpenAI(
            api_key=server_config.api_key,
            base_url=server_config.url,
        )
        
        response = await client.models.list()
        models = response.model_dump()["data"]
        
        # 为每个模型添加服务器标识
        for model in models:
            model["id"] = f"[{server_alias}]{model['id']}"
        
        return models
    except Exception as e:
        logger.error(f"从服务器 {server_alias} 获取模型列表失败: {str(e)}")
        return []

@app.get("/v1/models")
async def list_models(request: Request):
    """获取所有配置的服务器的模型列表"""
    try:
        # 并发获取所有服务器的模型列表
        tasks = []
        for server_alias, server_config in config.servers.items():
            task = fetch_models_from_server(server_alias, server_config)
            tasks.append(task)
        
        # 等待所有请求完成
        models_lists = await asyncio.gather(*tasks)
        
        # 合并所有模型列表
        all_models = []
        for models in models_lists:
            all_models.extend(models)
        
        return Response(
            content=json.dumps({"data": all_models, "object": "list"}),
            media_type="application/json"
        )
    except Exception as e:
        logger.error(f"获取模型列表失败: {str(e)}")
        return Response(
            content=json.dumps({"error": str(e)}),
            media_type="application/json",
            status_code=500
        )

async def proxy_request(request: Request, target_url: str, server_alias: Optional[str] = None) -> Response:
    """代理请求到目标服务器"""
    # 读取原始请求内容
    body = await request.json()
    headers = dict(request.headers)
    
    try:
        # 获取API密钥
        api_key = get_api_key(headers, server_alias)
        
        is_stream = body.get("stream", False)
        # 从model字段中提取真实的模型名称
        body["model"] = extract_real_model_name(body["model"])

        del body["stream_options"]  # openai 不支持stream_options字段

        # 创建OpenAI客户端
        client = AsyncOpenAI(
            api_key=api_key,
            base_url=target_url
        )
        
        if "/chat/completions" in request.url.path:
            if is_stream:
                # 流式响应
                # stream = await client.chat.completions.create(
                #     model=body["model"],
                #     messages=body["messages"],
                #     stream=True
                # )
                stream = await client.chat.completions.create(**body)
                
                async def generate():
                    try:
                        async for chunk in stream:
                            yield f"data: {chunk.model_dump_json()}\n\n"
                    except Exception as e:
                        logger.error(f"流式响应生成失败: {str(e)}")
                        yield f"data: {json.dumps({'error': str(e)})}\n\n"
                    finally:
                        yield "data: [DONE]\n\n"
                
                return StreamingResponse(
                    generate(),
                    media_type="text/event-stream"
                )
            else:
                # 非流式响应
                response = await client.chat.completions.create(**body)
                response_data = response.model_dump()
                await log_request_response(body, response_data, target_url, is_stream)
                return Response(
                    content=json.dumps(response_data),
                    media_type="application/json"
                )
        else:
            # 其他API端点暂不支持
            return Response(
                content=json.dumps({"error": "Unsupported API endpoint"}),
                media_type="application/json",
                status_code=400
            )
                
    except ValueError as e:
        return Response(
            content=json.dumps({"error": str(e)}),
            media_type="application/json",
            status_code=401
        )
    except Exception as e:
        logger.error(f"代理请求失败: {str(e)}")
        return Response(
            content=json.dumps({"error": str(e)}),
            media_type="application/json",
            status_code=500
        )

@app.post("/v1/{path:path}")
async def proxy_openai(request: Request, path: str):
    """处理所有OpenAI API请求的主路由"""
    try:
        body = await request.json()
        proxy_url = request.query_params.get("proxy")
        model = body.get("model", "")
        
        target_url, server_alias = parse_target_url(model, proxy_url)
        if not target_url.endswith("/v1"):
            target_url = f"{target_url.rstrip('/')}/v1"
            
        return await proxy_request(request, target_url, server_alias)
        
    except Exception as e:
        logger.error(f"处理请求失败: {str(e)}")
        return Response(
            content=json.dumps({"error": str(e)}),
            media_type="application/json",
            status_code=500
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 