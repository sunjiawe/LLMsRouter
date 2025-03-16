# LLMsRouter

<div align="center">

[![GitHub stars](https://img.shields.io/github/stars/sunjiawe/LLMsRouter?style=social)](https://github.com/sunjiawe/LLMsRouter/stargazers)
[![License](https://img.shields.io/github/license/sunjiawe/LLMsRouter)](https://github.com/sunjiawe/LLMsRouter/blob/main/LICENSE)
[![Python Version](https://img.shields.io/badge/python-3.8%2B-blue)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.95.0%2B-009688)](https://fastapi.tiangolo.com/)
[![Docker](https://img.shields.io/badge/docker-supported-2496ED)](https://www.docker.com/)

<img src="img/logo.png" alt="LLMsRouter Logo" width="200"/>

**一站式管理你手上的大模型(LLM)提供商，在模型之间轻松、无缝切换**

[English](./README_EN.md) | 中文文档

</div>

## 🔍 使用场景

- **企业本地部署运营管理** - 很多企业在追求本地部署，那么部署之后如何管理呢？LLMsRouter为团队提供统一的 OpenAI-API 访问点，同时实现用户级别的权限控制和使用追踪。开启用户管理，可为每个员工/服务创建单独的帐号。

- **揭秘 Prompt 魔法** - 通过 Langfuse 轻松揭秘各种 AI 应用背后的 prompt 魔法 (前提条件：应用支持接入第三方 OpenAI API)

- **开发中轻松切换提供商** - 有没有遇到这种烦恼：在开发大模型应用有时需要切换不同的模型或不同的提供商，来对比模型的效果。目前，并不是所有框架都对模型切换有很好的支持。使用 LLMsRouter 的 User-Bypass 功能，可以轻松在多个提供商之间实时切换模型。(受够了换一次模型，要重新运行一次代码！！)

- **多个提供商接入单个API配置** - 有些AI工具只支持配置一个 OpenAI 兼容的服务商。使用LLMsRouter，可以把多个服务商同时接入(通过自定义的 model 字段控制调用哪一个)。

## ✨ 特性

- 🔄 **多服务商统一管理** - 任意OpenAI兼容的模型都可以接入，并用一个统一的 OpenAI兼容端口对外提供服务
- 🌊 **流式响应支持** - 支持 stream 模式，实时获取模型响应
- 🔍 **灵活路由模式**
  - 🔹 **【推荐】Auto 模式** - 通过自定义模型名称进行路由 `[provider]model_name`  provider是配置文件中定义的别名
  - 🔹 **Proxy 模式** - 通过 URL 参数指定目标服务器。本模式兼容性不好
- 📊 **Langfuse 集成** - 轻松追踪和分析 API 请求，监控 tokens 消耗
- 👥 **用户管理系统** - 用户认证和权限控制，适合企业内部部署
- 🐳 **Docker 支持** - 简化部署和维护


## 🚀 快速开始

### 安装

```bash
# 克隆仓库
git clone https://github.com/sunjiawe/LLMsRouter.git
cd LLMsRouter

# 安装依赖
pip install -r requirements.txt

# 配置服务
cp config.yaml.template config.yaml
# 编辑 config.yaml 添加你的服务商信息
```

### 配置

编辑 `config.yaml` 文件，添加你的 LLM 服务商信息：

```yaml
servers:
  openai:
    url: "https://api.openai.com/v1"
    api_key: "sk-your-openai-key"
    filter: "gpt"  # 只显示包含 gpt 的模型
  
  anthropic:
    url: "https://api.anthropic.com/v1"
    api_key: "your-anthropic-key"
    override: ["claude-3-opus-20240229", "claude-3-sonnet-20240229"]
  
  deepseek:
    url: "http://your-deepseek-server:8000/v1"
    api_key: "your-deepseek-key"
    append: ["deepseek-chat", "deepseek-coder"]
```

这里的 provider 名称可以随便填，简短、有辨识度即可


### 运行

```bash
python main.py
```

服务将在 `http://localhost:8000` 启动。

## 📖 详细使用指南

### Auto 模式 (推荐)

在模型名称中嵌入目标服务器，格式为 `[server]model_name`：

```bash
curl http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your-api-key" \
  -d '{
    "model": "[openai]gpt-4",
    "messages": [{"role": "user", "content": "解释量子计算的基本原理"}]
  }'
```

未开启用户管理时，随便填写一个 api-key。

### Proxy 模式

通过 URL 参数指定目标服务器：

```bash
curl http://localhost:8000/v1/chat/completions?proxy=openai \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your-api-key" \
  -d '{
    "model": "gpt-4",
    "messages": [{"role": "user", "content": "解释量子计算的基本原理"}]
  }'
```

### 在大模型应用中使用

在支持 OpenAI兼容 API 的AI应用中（如 Cursor、Claude、Open WebUI 等），将 API URL 设置为：

```
http://localhost:8000/v1
```

然后在使用时，通过模型名称指定服务商：`[openai]gpt-4`、`[anthropic]claude-3-opus-20240229` 等。

> 如果是服务器部署/docker部署，将localhost替换为服务器IP

## 🔧 进阶配置

### Langfuse 集成

LLMsRouter 支持与 [Langfuse](https://langfuse.com) 集成，用于追踪和分析 API 请求。

1. 在 Langfuse 官网注册账号并创建项目
2. 获取 `LANGFUSE_SECRET_KEY` 和 `LANGFUSE_PUBLIC_KEY`
3. 创建 `.env` 文件并添加以下内容：

```bash
LANGFUSE_SECRET_KEY=your-secret-key
LANGFUSE_PUBLIC_KEY=your-public-key
LANGFUSE_HOST=https://cloud.langfuse.com  # 或自建服务器地址
```

### 用户管理系统

启用用户管理后，所有 API 请求都需要进行用户认证。

#### 启用用户管理

```bash
# 在 .env 文件中添加
ENABLE_ACCOUNT_MANAGEMENT=true
```

#### 用户管理命令

```bash
# 添加用户
python manage.py add username --email user@example.com

# 设置用户权限
python manage.py add username --permissions "openai,anthropic"

# 列出所有用户
python manage.py list

# 修改用户权限
python manage.py modify username --permissions "openai,deepseek"

# 批量导入用户
python manage.py import users.csv
```

## 🐳 Docker 部署

### 自行构建镜像

```bash
docker build -t llmsrouter:latest .

docker run -d --name llmsrouter \
  -p 8000:8000 \
  --network host \
  --env-file .env \
  -v $(pwd)/config.yaml:/app/config.yaml \
  llmsrouter:latest
```

## 📊 架构

```
┌─────────────┐     ┌───────────────┐     ┌─────────────────┐
│ 客户端工具   │────▶│   LLMsRouter  │────▶│  OpenAI API     │
│ (Claude等)   │     │               │     └─────────────────┘
└─────────────┘     │   ┌─────────┐ │     ┌─────────────────┐
                    │   │ 路由层   │ │────▶│  Anthropic API  │
┌─────────────┐     │   └─────────┘ │     └─────────────────┘
│ OpenAI SDK  │────▶│   ┌─────────┐ │     ┌─────────────────┐
│ 应用        │     │   │用户管理 │ │────▶│  自部署模型 API  │
└─────────────┘     │   └─────────┘ │     └─────────────────┘
                    └───────┬───────┘
                            │
                    ┌───────▼───────┐
                    │   Langfuse    │
                    │  (请求追踪)   │
                    └───────────────┘
```

## 📝 配置文件详解

`config.yaml` 配置选项：

| 选项 | 说明 | 示例 |
|------|------|------|
| `url` | 大模型提供商的 API 基础 URL | `https://api.openai.com/v1` |
| `api_key` | 大模型提供商的 API 密钥 | `provider-api-key` |
| `filter` | 过滤/models的结果 | `gpt*` 或 `gpt free` |
| `append` | 在 API 返回的模型列表后追加指定模型 | `["custom-model"]` |
| `override` | 手动指定模型列表，设置后跳过 API 请求 | `["model1", "model2"]` |


罗列一些不错的 LLM API 提供商：
- [DeepSeek](https://platform.deepseek.com/)
- [阿里百炼](https://bailian.console.aliyun.com/#/model-market)
- [字节火山云](https://console.volcengine.com/ark)
- [OpenRouter](https://openrouter.ai/models)
- [硅基流动](https://cloud.siliconflow.cn/models)


## 🤝 贡献

欢迎提交 Pull Request 或创建 Issue！

## 📄 许可证

[MIT License](LICENSE)

## 🙏 致谢

- [Cursor](https://cursor.sh/) - 强大的 AI 辅助开发工具
- [Langfuse](https://langfuse.com/) - LLM 应用监控平台
- [FastAPI](https://fastapi.tiangolo.com/) - 高性能 API 框架
