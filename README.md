# OpenAI API 转发路由服务

LLMsRouter 是一个基于 FastAPI 的 OpenAI API 转发服务，支持将 OpenAI 兼容的 API 请求转发到不同的目标服务器。

## 功能特点

- 转发 OpenAI 兼容的 API 请求，可以集成多个LLM Provider
- 支持流式响应（stream mode）
- 两种转发模式：
  - Proxy 模式：通过 URL 参数指定目标服务器
  - Auto 模式：通过模型名称指定目标服务器（格式：[server]model_name）


## 安装

1. 克隆仓库
```bash
git clone https://github.com/sunjiawe/LLMsRouter.git
```

2. 安装依赖：
```bash
pip install -r requirements.txt
```

3. 配置 config.yaml

将config.yaml.template重命名为`config.yaml`，并根据需要配置API 服务商的API Key。


## 运行

```bash
python main.py
```

服务将在 `http://localhost:8000` 启动。

## 使用方法

### Proxy 模式

通过 URL 参数指定目标服务器：

```bash
curl http://localhost:8000/v1/chat/completions?proxy=https://target-server.com \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-3.5-turbo",
    "messages": [{"role": "user", "content": "Hello!"}]
  }'
```

### Auto 模式

在模型名称中嵌入目标服务器：

```bash
curl http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "[https://target-server.com]gpt-3.5-turbo",
    "messages": [{"role": "user", "content": "Hello!"}]
  }'
```

## 日志

日志文件位于 `api_proxy.log`，记录所有请求和响应的详细信息。 