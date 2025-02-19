# OpenAI API 转发路由服务

LLMsRouter 是一个基于 FastAPI 的 OpenAI API 转发服务，支持将 OpenAI 兼容的 API 请求转发到不同的目标服务器。

这个项目的初衷：
- 使用Cline时，只能配置一个 OpenAI兼容的URL。利用LLMsRouter可以中继多个LLM服务商。且集成Langfuse在单个WEB UI中查看多个服务器的tokens消耗。 (虽然后面发现了Roo Code支持多个配置切换)
- 对于一些 agnet 工具或插件，想了解其背后的prompt tricks，需要去看源码。 通过 LLMsRouter with Langfuse，可以轻松的查看到这些agent工具背后的 prompt 工程。


功能特性：
- 在一个OpenAI API Config下集成多个LLM Provider
- 转发 OpenAI 兼容的 API 请求，通过配置文件管理LLM Provider的API Key
- 支持流式响应（stream mode）
- 两种转发模式：
  - Proxy 模式：通过 URL 参数指定目标服务器
  - Auto 模式：通过模型名称指定目标服务器（格式：[server]model_name）
- 支持Langfuse的API请求追踪(Trace)
  - 可以轻松统计不同 API Provider 的 tokens 消耗
  - 帮助你调试 agent 工具的调用链路、prompt tricks

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

将config.yaml.template重命名为`config.yaml`，并根据需要配置服务商信息。配置文件结构如下：

```yaml
servers:
  # 服务器别名
  server_alias:
    url: "服务器URL"
    api_key: "API密钥"
    filter: "模型过滤条件"    # 可选，支持多个条件（空格分隔）和*通配符
    override: ["model1", "model2"]  # 可选，手动指定模型列表，设置后将跳过API请求
    append: ["model3", "model4"]    # 可选，在API返回的模型列表后追加指定模型

```

配置说明：
- `url`: 服务器的API基础URL
- `api_key`: 服务器的API密钥
- `filter`: （可选）模型过滤条件
  - 支持多个条件，用空格分隔，例如 "gpt free" 表示模型名称同时包含 gpt 和 free
  - 支持 * 通配符，例如 "gpt*" 表示以 gpt 开头的模型
- `override`: （可选）手动指定模型列表
  - 如果设置此字段，将不会请求服务器的 /models 接口
  - 直接使用指定的模型列表
- `append`: （可选）追加模型
  - 这些模型会被添加到从API获取的模型列表后面
  - 本字段不受filter字段的影响

示例配置：
```yaml
servers:
  local_llm:
    url: "http://localhost:8000/v1"
    api_key: "your-api-key"
    filter: "llama vicuna"  # 只显示同时包含 llama 和 vicuna 的模型
    append: ["custom-model"]  # 追加自定义模型

  openai:
    url: "https://api.openai.com/v1"
    api_key: "your-openai-key"
    filter: "gpt"  # 只显示包含 gpt 的模型
    
  custom_server:
    url: "https://custom-server.com/v1"
    api_key: "your-key"
    override: ["model1", "model2"]  # 手动指定可用模型
```

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

## Langfuse

可以去官网注册一个账号，然后创建一个项目，获取到 `LANGFUSE_SECRET_KEY` 和 `LANGFUSE_PUBLIC_KEY`，然后配置到 `.env` 文件中。

也可以 [自建Langfuse Server](https://langfuse.com/self-hosting) ，并修改`.env`文件中的 `LANGFUSE_HOST` 的IP。


## 日志

日志文件位于 `api_proxy.log`，记录所有请求和响应的详细信息。 