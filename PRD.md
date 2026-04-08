# RAG 智能知识库 — 产品规格书
**版本**: 2.0  
**日期**: 2026-04-01  
**状态**: 开发中  
**产品定位**: 企业级多租户 SaaS 知识库平台
---
## 1. 产品概述
RAG 智能知识库是一套基于检索增强生成（Retrieval-Augmented Generation）技术的企业级知识管理平台。系统支持多格式文档解析、向量化存储、语义检索与 AI 问答，并提供知识库共享市场、订阅计费、游客体验等商业化能力，满足个人用户到企业团队的多元化需求。
### 1.1 核心价值
| 价值维度 | 描述 |
|----------|------|
| 私有化部署 | 数据不出内网，完整运行于 Docker 容器 |
| 多格式支持 | 覆盖文本、PDF、Office、图片、音视频等 20+ 格式 |
| 多租户架构 | 用户级数据隔离，支持团队协作与权限管理 |
| 知识库市场 | 用户可发布、发现、使用他人共享的优质知识库 |
| 灵活模型 | 支持 OpenAI、通义千问、DeepSeek、智谱、Ollama 等，运行时切换 |
| 商业化能力 | 会员订阅、知识库付费、游客体验模式 |
---
## 2. 技术架构
### 2.1 系统架构
```
┌─────────────────┐     HTTP/Proxy      ┌──────────────────────┐
│   前端 (React)   │ ─────────────────► │  后端 (FastAPI)       │
│   Vite + React  │                    │  Uvicorn / Python 3.11│
│   Port 3000     │                    │  Port 8000            │
└─────────────────┘                    └──────┬───────────────┘
                                             │
┌───────────────────┼────────────────┐
▼                   ▼                ▼
SQLite (aiosqlite)   ChromaDB         文件存储
用户/知识库/订单      向量索引          uploads/
```
### 2.2 技术栈
| 层级 | 技术选型 |
|------|----------|
| 前端框架 | React 18 + Vite 5 + React Router v6 |
| HTTP 客户端 | Axios |
| 后端框架 | FastAPI + Uvicorn |
| 异步 ORM | SQLAlchemy 2.0 (async) + aiosqlite |
| 向量数据库 | ChromaDB 0.4 |
| 认证鉴权 | JWT (python-jose) + bcrypt |
| 容器化 | Docker + Docker Compose |
| 扩展服务 | 百度 OCR、邮件服务、短信服务、支付网关 |
### 2.3 核心数据模型
```
User
├── id, username, email, phone
├── hashed_password, tier (free/pro/enterprise)
├── expires_at, is_active, is_admin
└── created_at, updated_at
Tier (会员等级)
├── code (free/pro/enterprise)
├── name, description, price, duration_days
├── features (JSON: max_kb, max_docs, max_chat, ocr_enabled, market_enabled)
└── created_at
KnowledgeBase
├── id, name, description, owner_id
├── collection_name, is_public, is_market_published
├── document_count, total_chunks, usage_count
└── created_at, updated_at
MarketListing (市场发布)
├── id, kb_id, title, description, cover_image
├── price, is_free, category, tags (JSON)
├── rating, review_count, download_count
└── published_at, status
Payment
├── id, user_id, amount, currency, status
├── payment_method, transaction_id
├── description, created_at, completed_at
KnowledgeBaseAccess
├── id, kb_id, user_id, access_type (owner/public/purchased)
├── purchased_at, expires_at
Document
├── id, kb_id, filename, file_type, file_size
├── status, chunk_count, error_message
└── created_at, processed_at
Conversation & Message
├── id, user_id, kb_id, role (user/assistant/guest)
├── content, sources (JSON), metadata
└── created_at
```
---
## 3. 功能规格
### 3.1 用户认证与会员体系
| 功能 | 描述 |
|------|------|
| 注册/登录 | 用户名 + 邮箱/手机 + 密码，JWT Token 有效期 24h |
| 会员等级 | Free（免费）/ Pro（专业）/ Enterprise（企业） |
| 权益控制 | 不同等级限制知识库数量、文档数量、对话次数、高级功能 |
| 会员过期 | 到期后自动降级，保留数据但限制写入 |
### 3.2 知识库管理
| 功能 | 描述 |
|------|------|
| 创建/编辑 | 填写名称、描述，自动创建 ChromaDB Collection |
| 权限控制 | 私有（仅创建者）/ 公开（所有人可读）/ 付费购买 |
| 删除 | 级联删除文档、向量数据、关联订单 |
| 数据统计 | 文档数、向量块数、被访问次数、被收藏/下载次数 |
### 3.3 文档上传与处理
#### 支持格式
| 类别 | 扩展名 | 处理方式 |
|------|--------|----------|
| 纯文本 | .txt, .md, .csv, .json, .log, .xml, .yaml, .yml | 直接读取 |
| PDF | .pdf | PyMuPDF / pdfplumber 提取 |
| Word | .docx, .doc | python-docx 解析 |
| Excel | .xlsx, .xls | openpyxl / pandas 解析 |
| PowerPoint | .pptx, .ppt | python-pptx 提取 |
| 图片 (OCR) | .png, .jpg, .jpeg, .gif, .bmp, .webp | Tesseract / 百度 OCR |
| 音频 | .mp3, .wav, .m4a, .ogg, .flac | Whisper 语音转文字 |
| 视频 | .mp4, .avi, .mkv, .mov, .wmv, .webm | FFmpeg 提取音频 → Whisper |
#### 处理流程
```
上传文件 → 格式识别 → 解析文本 → 文本分块 → Embedding → 存入 ChromaDB
```
- **分块策略**: chunk_size=1000 字符，overlap=200 字符
- **文件大小限制**: 默认 100MB（可配置）
- **OCR 引擎**: 支持 Tesseract（本地）与百度 OCR（API）双引擎
- **状态追踪**: pending → processing → completed / failed
### 3.4 智能问答
#### RAG 流程
```
用户提问
→ ChromaDB 相似度检索 (top_k=5)
→ 拼接上下文 + 历史对话
→ LLM 生成回答
→ 返回答案 + 引用来源
```
| 参数 | 默认值 | 说明 |
|------|--------|------|
| top_k | 5 | 检索文档块数量 |
| temperature | 0.7 | 生成多样性 |
| max_tokens | 2000 | 最大回答长度 |
| 历史对话 | 最近 6 条 | 保持上下文连贯 |
- 回答语言自动跟随提问语言
- 引用标注格式: `[Document N]`
- 支持 SSE 流式输出
- 支持游客模式（有限次数体验）
### 3.5 知识库市场
| 功能 | 描述 |
|------|------|
| 发布知识 | 将知识库设为公开或定价出售 |
| 浏览市场 | 按分类、标签、评分、下载量筛选 |
| 详情展示 | 介绍、预览、价格、评价 |
| 购买授权 | 支付后获得使用权限，支持限时/永久 |
| 评价系统 | 用户对购买的知识库进行评分与评论 |
### 3.6 支付系统
| 功能 | 描述 |
|------|------|
| 会员订阅 | Pro / Enterprise 包月/包年 |
| 单次购买 | 付费知识库单次购买 |
| 支付方式 | 支持多种支付网关接入（支付宝/微信/Stripe） |
| 订单管理 | 订单状态追踪、退款处理、发票申请 |
### 3.7 模型配置
运行时切换，无需重启服务，支持前端可视化配置。
#### 支持的 LLM 服务商
| 服务商 | Base URL | 默认模型 |
|--------|----------|----------|
| OpenAI | https://api.openai.com/v1 | gpt-4o-mini |
| DeepSeek | https://api.deepseek.com/v1 | deepseek-chat |
| 通义千问 | https://dashscope.aliyuncs.com/compatible-mode/v1 | qwen-plus |
| 智谱 AI | https://open.bigmodel.cn/api/paas/v4/ | glm-4-flash |
| Ollama（本地） | http://host.docker.internal:11434/v1 | qwen2.5:7b |
| 自定义 | 用户填写 | 用户填写 |
#### 支持的 Embedding 服务商
| 服务商 | 默认模型 |
|--------|----------|
| OpenAI | text-embedding-3-small |
| 通义千问 | text-embedding-v3 |
| 智谱 AI | embedding-3 |
| Ollama | nomic-embed-text |
> ⚠️ 切换 Embedding 模型后，已有知识库需重新上传索引。
### 3.8 管理员后台
| 功能 | 描述 |
|------|------|
| 用户管理 | 查看、封禁、调整会员等级 |
| 内容审核 | 审核市场发布的知识库 |
| 订单管理 | 查看所有交易记录，处理退款 |
| 系统监控 | 在线用户数、API 调用量、存储使用量 |
---
## 4. API 接口
### 基础路径: `/api`
| 模块 | 方法 | 路径 | 描述 | 权限 |
|------|------|------|------|------|
| 认证 | POST | /auth/register | 注册 | 公开 |
| 认证 | POST | /auth/login | 登录 | 公开 |
| 认证 | GET | /auth/me | 当前用户 | 登录 |
| 知识库 | GET | /kb/ | 知识库列表 | 登录 |
| 知识库 | POST | /kb/ | 创建知识库 | 登录 |
| 知识库 | GET | /kb/{id} | 知识库详情 | 登录/公开 |
| 知识库 | PUT | /kb/{id} | 更新知识库 | 所有者 |
| 知识库 | DELETE | /kb/{id} | 删除知识库 | 所有者 |
| 文档 | POST | /kb/{id}/upload | 上传文档 | 所有者 |
| 文档 | DELETE | /kb/{id}/documents/{doc_id} | 删除文档 | 所有者 |
| 问答 | POST | /chat/ | 发送问题 | 登录/游客 |
| 问答 | POST | /chat/stream | 流式问答 | 登录/游客 |
| 对话 | GET | /chat/conversations | 对话列表 | 登录 |
| 市场 | GET | /market/ | 浏览市场 | 公开 |
| 市场 | POST | /market/publish | 发布知识 | 登录 |
| 市场 | POST | /market/purchase | 购买授权 | 登录 |
| 支付 | POST | /payment/create | 创建订单 | 登录 |
| 支付 | GET | /payment/status/{id} | 订单状态 | 登录 |
| 配置 | GET | /settings/model | 获取模型配置 | 登录 |
| 配置 | PUT | /settings/model | 更新模型配置 | 登录 |
| 统计 | GET | /stats/ | 全局统计 | 登录 |
| 其他 | GET | /health | 健康检查 | 公开 |
| 其他 | GET | /supported-formats | 支持格式列表 | 公开 |
---
## 5. 部署规格
### 5.1 环境要求
| 组件 | 最低配置 | 推荐配置 |
|------|----------|----------|
| Docker | >= 20.x | >= 24.x |
| 内存 | 4GB | 8GB+ |
| 磁盘 | 10GB | 50GB+ |
| CPU | 2 核 | 4 核+ |
### 5.2 核心环境变量
| 变量 | 默认值 | 说明 |
|------|--------|------|
| SECRET_KEY | — | JWT 签名密钥（生产必须修改） |
| DATABASE_URL | sqlite+aiosqlite:///./data/app.db | 数据库连接 |
| CHROMA_PERSIST_DIR | ./data/chroma_db | 向量数据目录 |
| UPLOAD_DIR | ./uploads | 文件上传目录 |
| MAX_FILE_SIZE_MB | 100 | 文件大小限制 |
| CHUNK_SIZE | 1000 | 分块大小 |
| CHUNK_OVERLAP | 200 | 分块重叠 |
| WHISPER_MODEL | base | Whisper 模型大小 |
### 5.3 持久化数据
| 路径 | 内容 |
|------|------|
| backend/data/app.db | SQLite 主数据库 |
| backend/data/chroma_db/ | ChromaDB 向量索引 |
| backend/data/model_config.json | 模型配置 |
| backend/uploads/ | 原始文件存储 |
---
## 6. 已知限制与风险
| 限制 | 影响 | 缓解方案 |
|------|------|----------|
| 单机架构 | SQLite 不支持横向扩展 | 后续可迁移至 PostgreSQL |
| 音视频转写 | ARM 架构下 Whisper 较慢 | 使用 smaller 模型或 API 服务 |
| Embedding 切换 | 模型切换后需重新索引 | 提示用户备份，提供一键重建功能 |
| 并发处理 | 文档处理为串行队列 | 引入 Celery/Redis 异步任务队列 |
| OCR 质量 | 依赖图片清晰度与引擎 | 提供双引擎（Tesseract + 百度 OCR） |
---
## 7. 未来规划
| 阶段 | 功能 |
|------|------|
| V2.1 | PostgreSQL 支持、Redis 缓存、异步任务队列 |
| V2.2 | 团队协作、细粒度权限（RBAC）、知识库版本控制 |
| V2.3 | Webhook 集成、API 开放平台、第三方插件市场 |
| V3.0 | 多模态 RAG（图片/音视频直接问答）、Agent 模式 |
