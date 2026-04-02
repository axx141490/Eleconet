# RAG 智能知识库 — 产品规格书

**版本**: 1.0  
**日期**: 2026-04-01  
**状态**: 开发中

---

## 1. 产品概述

RAG 智能知识库是一套基于检索增强生成（Retrieval-Augmented Generation）技术的私有化问答系统。用户可将企业或个人文档上传至系统，通过自然语言提问，获得基于文档内容的精准回答，并支持引用溯源。

### 1.1 核心价值

- **私有化部署**：数据不出内网，完整运行于 Docker 容器
- **多格式支持**：覆盖文本、PDF、Office 文档、图片、音视频等主流格式
- **模型灵活配置**：支持 OpenAI、DeepSeek、通义千问、智谱 AI、本地 Ollama 等多种 LLM/Embedding 服务商，运行时切换无需重启
- **多用户隔离**：每个账户拥有独立知识库，数据互不干扰

---

## 2. 技术架构

### 2.1 系统架构

```
┌─────────────────┐     HTTP/Proxy      ┌──────────────────────┐
│   前端 (React)   │ ─────────────────► │  后端 (FastAPI)       │
│   Vite Dev      │                    │  Uvicorn / Python 3.11│
│   Port 3000     │                    │  Port 8000            │
└─────────────────┘                    └──────┬───────────────┘
                                              │
                          ┌───────────────────┼────────────────┐
                          ▼                   ▼                ▼
                    SQLite (aiosqlite)   ChromaDB         文件存储
                    用户/知识库/对话      向量索引          uploads/
```

### 2.2 技术栈

| 层级 | 技术 |
|------|------|
| 前端框架 | React 18 + Vite 5 |
| 前端路由 | React Router v6 |
| HTTP 客户端 | Axios |
| 后端框架 | FastAPI + Uvicorn |
| 异步 ORM | SQLAlchemy 2.0 (async) + aiosqlite |
| 向量数据库 | ChromaDB 0.4 |
| 认证 | JWT (python-jose) + bcrypt |
| 容器化 | Docker + Docker Compose |

### 2.3 数据模型

```
User
 ├── id, username, email, hashed_password
 ├── is_active, is_admin
 └── created_at, updated_at

KnowledgeBase
 ├── id, name, description, owner_id
 ├── collection_name (ChromaDB collection)
 ├── document_count, total_chunks
 └── created_at, updated_at

Document
 ├── id, kb_id, filename, file_type, file_size
 ├── status (pending/processing/completed/failed)
 ├── chunk_count, error_message
 └── created_at, processed_at

Conversation
 ├── id, user_id, kb_id, title
 └── created_at, updated_at

Message
 ├── id, conversation_id, role (user/assistant)
 ├── content, sources (JSON)
 └── created_at
```

---

## 3. 功能规格

### 3.1 用户认证

| 功能 | 描述 |
|------|------|
| 注册 | 用户名 + 邮箱 + 密码，注册后立即返回 JWT Token |
| 登录 | 用户名 + 密码，返回 JWT Token |
| Token 有效期 | 默认 1440 分钟（24 小时） |
| 自动登出 | 请求返回 401 时自动清除本地 Token 并跳转登录页 |

### 3.2 知识库管理

| 功能 | 描述 |
|------|------|
| 创建知识库 | 填写名称和描述，系统自动创建对应 ChromaDB collection |
| 查看知识库列表 | 按更新时间倒序，显示文档数和向量块数 |
| 知识库详情 | 显示文档列表及各文档处理状态 |
| 删除知识库 | 同时删除所有文档文件、ChromaDB 数据和数据库记录 |

### 3.3 文档上传与处理

#### 支持格式

| 类别 | 扩展名 |
|------|--------|
| 纯文本 | .txt, .md, .csv, .json, .log, .xml, .yaml, .yml |
| PDF | .pdf |
| Word | .docx, .doc |
| Excel | .xlsx, .xls |
| PowerPoint | .pptx, .ppt |
| 图片 (OCR) | .png, .jpg, .jpeg, .gif, .bmp, .webp |
| 音频 | .mp3, .wav, .m4a, .ogg, .flac |
| 视频 | .mp4, .avi, .mkv, .mov, .wmv, .webm |

#### 处理流程

```
上传文件 → 解析文本 → 文本分块 → Embedding 向量化 → 存入 ChromaDB
```

- **分块策略**：默认 chunk_size=1000 字符，overlap=200 字符
- **文件大小限制**：默认 100MB
- **图片处理**：通过 Tesseract OCR 提取文字（支持中文简体）
- **音视频处理**：通过 OpenAI Whisper 语音转文字后再处理

### 3.4 智能问答

#### RAG 流程

```
用户提问
  → ChromaDB 相似度检索 (top_k=5)
  → 拼接上下文 + 历史对话
  → 调用 LLM 生成回答
  → 返回答案 + 引用来源
```

| 参数 | 默认值 | 说明 |
|------|--------|------|
| top_k | 5 | 检索文档块数量 |
| temperature | 0.7 | 生成多样性 |
| max_tokens | 2000 | 最大回答长度 |
| 历史对话 | 最近 6 条 | 保持上下文连贯 |

- 回答语言自动跟随提问语言（中文问题 → 中文回答）
- 回答中使用 `[Document N]` 格式标注引用来源
- 支持流式输出（SSE）

### 3.5 对话管理

- 自动创建对话，以问题前 80 字符为标题
- 支持跨会话继续对话（通过 conversation_id）
- 查看历史对话列表
- 删除对话记录

### 3.6 模型配置

运行时切换，无需重启服务。

#### 支持的 LLM 服务商

| 服务商 | Base URL | 默认模型 |
|--------|----------|----------|
| OpenAI | https://api.openai.com/v1 | gpt-4o-mini |
| DeepSeek | https://api.deepseek.com/v1 | deepseek-chat |
| 通义千问 (Qwen) | https://dashscope.aliyuncs.com/compatible-mode/v1 | qwen-plus |
| 智谱 AI (GLM) | https://open.bigmodel.cn/api/paas/v4/ | glm-4-flash |
| Ollama（本地） | http://host.docker.internal:11434/v1 | qwen2.5:7b |
| 自定义 | 用户填写 | 用户填写 |

#### 支持的 Embedding 服务商

| 服务商 | 默认模型 |
|--------|----------|
| OpenAI | text-embedding-3-small |
| 通义千问 | text-embedding-v3 |
| 智谱 AI | embedding-3 |
| Ollama | nomic-embed-text |

> ⚠️ 切换 Embedding 模型后，已有知识库数据与新模型不兼容，需重新上传文档。

### 3.7 仪表盘

展示全局统计：知识库数量、文档数量、对话数、用户数，以及支持的文件格式列表。

---

## 4. API 接口

### 基础路径：`/api`

| 模块 | 方法 | 路径 | 描述 |
|------|------|------|------|
| 认证 | POST | /auth/register | 注册 |
| 认证 | POST | /auth/login | 登录 |
| 认证 | GET | /auth/me | 当前用户信息 |
| 知识库 | GET | /kb/ | 知识库列表 |
| 知识库 | POST | /kb/ | 创建知识库 |
| 知识库 | GET | /kb/{id} | 知识库详情 |
| 知识库 | PUT | /kb/{id} | 更新知识库 |
| 知识库 | DELETE | /kb/{id} | 删除知识库 |
| 文档 | POST | /kb/{id}/upload | 上传文档 |
| 文档 | DELETE | /kb/{id}/documents/{doc_id} | 删除文档 |
| 文档 | GET | /kb/{id}/documents/{doc_id}/status | 文档处理状态 |
| 问答 | POST | /chat/ | 发送问题 |
| 问答 | POST | /chat/stream | 流式问答 |
| 对话 | GET | /chat/conversations | 对话列表 |
| 对话 | GET | /chat/conversations/{id} | 对话详情 |
| 对话 | DELETE | /chat/conversations/{id} | 删除对话 |
| 配置 | GET | /settings/model | 获取模型配置 |
| 配置 | PUT | /settings/model | 更新模型配置 |
| 配置 | GET | /settings/providers | 可用服务商列表 |
| 统计 | GET | /stats/ | 全局统计 |
| 其他 | GET | /health | 健康检查 |
| 其他 | GET | /supported-formats | 支持格式列表 |

---

## 5. 部署规格

### 5.1 环境要求

| 组件 | 版本 |
|------|------|
| Docker | >= 20.x |
| Docker Compose | >= 2.x |
| 内存 | >= 4GB（含 Whisper base 模型） |
| 磁盘 | >= 10GB |

### 5.2 环境变量（backend/.env）

| 变量 | 默认值 | 说明 |
|------|--------|------|
| SECRET_KEY | — | JWT 签名密钥，生产环境必须修改 |
| DATABASE_URL | sqlite+aiosqlite:///./data/app.db | 数据库连接 |
| CHROMA_PERSIST_DIR | ./data/chroma_db | 向量数据持久化目录 |
| UPLOAD_DIR | ./uploads | 文件上传目录 |
| MAX_FILE_SIZE_MB | 100 | 单文件大小限制 |
| CHUNK_SIZE | 1000 | 文本分块大小 |
| CHUNK_OVERLAP | 200 | 分块重叠字符数 |
| WHISPER_MODEL | base | Whisper 模型大小（tiny/base/small/medium） |

> 模型 API Key 现已通过前端「模型配置」页面管理，存储于 `data/model_config.json`，不再需要在 .env 中配置。

### 5.3 持久化数据

| 路径 | 内容 |
|------|------|
| backend/data/app.db | SQLite 数据库 |
| backend/data/chroma_db/ | ChromaDB 向量索引 |
| backend/data/model_config.json | 模型配置 |
| backend/uploads/ | 上传的原始文件 |

---

## 6. 已知限制

| 限制 | 说明 |
|------|------|
| 单机部署 | 使用 SQLite，不支持横向扩展 |
| 音视频转写 | 依赖 Whisper，ARM 架构下速度较慢 |
| Embedding 切换 | 切换模型后需重新索引所有文档 |
| 并发处理 | 文档处理为同步串行，大量文档上传时较慢 |
| OCR 质量 | 扫描版 PDF 识别精度依赖图片质量 |
