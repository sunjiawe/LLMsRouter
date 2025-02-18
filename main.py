from fastapi import FastAPI, Request, Response
from fastapi.responses import StreamingResponse
from openai import OpenAI, AsyncOpenAI
from loguru import logger
import json
from typing import Optional, Dict, Any
import os
from datetime import datetime
import asyncio

# 配置日志
logger.add("api_proxy.log", 
           format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}",
           rotation="500 MB")

app = FastAPI(title="OpenAI API Proxy Router")

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

def parse_target_url(model: str, proxy_url: Optional[str] = None) -> str:
    """解析目标URL
    支持两种模式：
    1. proxy模式：直接使用proxy_url参数
    2. auto模式：从model名称中解析，格式为[server]model_name
    """
    if proxy_url:
        return proxy_url
    
    if model.startswith("[") and "]" in model:
        server = model[1:model.index("]")]
        # 从model名称中移除服务器信息
        return server
    
    raise ValueError("无法确定目标服务器URL")

def extract_real_model_name(model: str) -> str:
    """从model字段中提取真实的模型名称"""
    if model.startswith("[") and "]" in model:
        return model[model.index("]") + 1:]
    return model

async def proxy_request(request: Request, target_url: str) -> Response:
    """代理请求到目标服务器"""
    # 读取原始请求内容
    body = await request.json()
    headers = dict(request.headers)
    
    # 获取API密钥
    api_key = headers.get("authorization", "").replace("Bearer ", "")
    if not api_key:
        return Response(
            content=json.dumps({"error": "Missing API key"}),
            media_type="application/json",
            status_code=401
        )
    
    is_stream = body.get("stream", False)
    # 从model字段中提取真实的模型名称
    body["model"] = extract_real_model_name(body["model"])
    
    try:
        # 创建OpenAI客户端
        client = AsyncOpenAI(
            api_key=api_key,
            base_url=target_url
        )
        
        if "/chat/completions" in request.url.path:
            if is_stream:
                # 流式响应
                stream = await client.chat.completions.create(
                    model=body["model"],
                    messages=body["messages"],
                    stream=True
                )
                
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
        
        target_url = parse_target_url(model, proxy_url)
        if not target_url.endswith("/v1"):
            target_url = f"{target_url.rstrip('/')}/v1"
            
        return await proxy_request(request, target_url)
        
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