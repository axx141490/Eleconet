# RAG 智能知识库问答系统

一个支持多种文件格式的 RAG (Retrieval-Augmented Generation) 智能知识库问答系统，基于 **FastAPI + React + ChromaDB + OpenAI** 构建。

## 系统特性

### 多格式文件支持
| 类别 | 格式 |
|------|------|
| 文本 | `.txt` `.md` `.csv` `.json` `.log` `.xml` `.yaml` |
| PDF | `.pdf` |
| Word | `.docx` `.doc` |
| Excel | `.xlsx` `.xls` |
| PPT | `.pptx` `.ppt` |
| 图片 | `.png` `.jpg` `.jpeg` `.gif` `.bmp` `.webp` (OCR + Vision) |
| 音频 | `.mp3` `.wav` `.m4a` `.ogg` `.flac` (Whisper 转录) |
| 视频 | `.mp4` `.avi` `.mkv` `.mov` `.wmv` `.webm` (提取音频 → 转录) |

### 核心功能
- **智能文件解析**：自动识别文件类型，使用对应解析器提取内容
- **向量化存储**：文本分块 → OpenAI Embedding → ChromaDB 存储
- **语义检索**：基于余弦相似度的向量检索，支持 top-k 参数
- **RAG 问答**：检索增强生成，LLM 基于上下文回答，引用来源
- **多轮对话**：支持对话历史，保持上下文连贯性
- **流式响应**：支持 SSE 流式输出，实时显示回答
- **知识库管理**：创建、编辑、删除知识库，上传和管理文档
- **用户认证**：JWT 认证，用户注册/登录
- **使用统计**：文档数、向量块数、对话数等统计数据

## 技术架构

```
┌─────────────┐     ┌──────────────┐     ┌──────────────┐
│  React 前端  │────▶│  FastAPI 后端  │────▶│   ChromaDB   │
│  (Vite)     │     │              │     │  (向量存储)    │
└─────────────┘     │  ┌──────────┐│     └──────────────┘
                    │  │文件解析器 ││
                    │  │ PDF/DOCX ││     ┌──────────────┐
                    │  │XLSX/PPTX ││────▶│   OpenAI API  │
                    │  │ IMG/AV   ││     │ Embedding+Chat│
                    │  └──────────┘│     └──────────────┘
                    │  ┌──────────┐│
                    │  │ SQLite DB ││     ┌──────────────┐
                    │  │用户/KB/对话││     │  Whisper API  │
                    │  └──────────┘│     │  (音频转录)    │
                    └──────────────┘     └──────────────┘
```

## 快速开始

### 前置要求
- Python 3.11+
- Node.js 18+
- OpenAI API Key
- (可选) ffmpeg - 视频文件支持
- (可选) tesseract - 图片 OCR 支持

### 方式一：脚本启动

```bash
# 1. 复制并配置环境变量
cp backend/.env.example backend/.env
# 编辑 backend/.env，填入 OPENAI_API_KEY

# 2. 一键启动
./start.sh
```

### 方式二：手动启动

```bash
# 后端
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # 编辑填入 OPENAI_API_KEY
uvicorn app.main:app --reload --port 8000

# 前端（新终端）
cd frontend
npm install
npm run dev
```

### 方式三：Docker

```bash
# 编辑 backend/.env
docker compose up --build
```

> **容器停止后重新启动**（不重新 build）：
> ```bash
> docker compose up -d
> ```
> 如需单独启动某个容器（以实际容器名为准）：
> ```bash
> # 容器名称参考
> # rag-knowledge-base-frontend-1
> # rag-knowledge-base-backend-1
> # rag-knowledge-base-nginx-1
> # rag-knowledge-base-certbot-1
> docker compose start frontend backend nginx certbot
> ```

> **开发提示**：若未改动 `Dockerfile` 或 `requirements.txt`，无需重新 build，直接重启即可：
> ```bash
> # 只改了后端 Python 代码
> docker compose restart backend
>
> # 只改了前端代码
> docker compose restart frontend
>
> # 前后端都改了
> docker compose restart backend frontend
> ```
> 只有改了 `Dockerfile`、`requirements.txt`（后端）或 `package.json`（前端）时才需要 `docker compose up --build`。

### 访问地址
- 前端界面：http://localhost:3000
- 后端 API：http://localhost:8000
- API 文档：http://localhost:8000/docs

## 项目结构

```
rag-knowledge-base/
├── backend/
│   ├── app/
│   │   ├── api/              # API 路由
│   │   │   ├── auth.py       # 用户认证
│   │   │   ├── knowledge_base.py  # 知识库管理
│   │   │   ├── chat.py       # 问答接口
│   │   │   ├── stats.py      # 统计接口
│   │   │   └── schemas.py    # Pydantic 模型
│   │   ├── core/             # 核心配置
│   │   │   ├── config.py     # 应用配置
│   │   │   ├── database.py   # 数据库连接
│   │   │   └── security.py   # JWT 认证
│   │   ├── models/           # 数据库模型
│   │   │   ├── user.py
│   │   │   ├── knowledge_base.py
│   │   │   └── conversation.py
│   │   ├── parsers/          # 文件解析器
│   │   │   ├── text_parser.py
│   │   │   ├── pdf_parser.py
│   │   │   ├── docx_parser.py
│   │   │   ├── xlsx_parser.py
│   │   │   ├── pptx_parser.py
│   │   │   ├── image_parser.py
│   │   │   ├── audio_video_parser.py
│   │   │   └── parser_factory.py
│   │   ├── services/         # 业务逻辑
│   │   │   ├── chunker.py    # 文本分块
│   │   │   ├── vector_store.py    # 向量存储
│   │   │   ├── rag_engine.py      # RAG 引擎
│   │   │   └── document_processor.py  # 文档处理
│   │   └── main.py           # FastAPI 入口
│   ├── requirements.txt
│   ├── Dockerfile
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── components/       # 通用组件
│   │   ├── pages/            # 页面组件
│   │   ├── services/         # API 服务
│   │   ├── hooks/            # React Hooks
│   │   └── styles/           # 全局样式
│   ├── package.json
│   └── Dockerfile
├── docker-compose.yml
├── start.sh
└── README.md
```

## API 接口

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/auth/register` | 用户注册 |
| POST | `/api/auth/login` | 用户登录 |
| GET | `/api/auth/me` | 获取当前用户 |
| GET | `/api/kb/` | 知识库列表 |
| POST | `/api/kb/` | 创建知识库 |
| GET | `/api/kb/{id}` | 知识库详情 |
| PUT | `/api/kb/{id}` | 更新知识库 |
| DELETE | `/api/kb/{id}` | 删除知识库 |
| POST | `/api/kb/{id}/upload` | 上传文件 |
| DELETE | `/api/kb/{id}/documents/{doc_id}` | 删除文档 |
| POST | `/api/chat/` | 发送问题 |
| POST | `/api/chat/stream` | 流式问答 |
| GET | `/api/chat/conversations` | 对话列表 |
| GET | `/api/chat/conversations/{id}` | 对话详情 |
| GET | `/api/stats/` | 系统统计 |

## 配置说明

编辑 `backend/.env` 文件：

```env
# 必填 - OpenAI API 密钥
OPENAI_API_KEY=sk-your-key-here

# 可选 - 自定义模型
OPENAI_EMBEDDING_MODEL=text-embedding-3-small
OPENAI_CHAT_MODEL=gpt-4o-mini

# 可选 - 分块参数
CHUNK_SIZE=1000
CHUNK_OVERLAP=200
```
