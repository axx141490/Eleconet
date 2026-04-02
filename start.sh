#!/bin/bash
# ===================================================
# RAG 智能知识库 - 快速启动脚本
# ===================================================

set -e

echo "🚀 RAG 智能知识库系统 - 启动中..."
echo ""

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "❌ 需要 Python 3.11+。请先安装 Python。"
    exit 1
fi

# Check Node
if ! command -v node &> /dev/null; then
    echo "❌ 需要 Node.js 18+。请先安装 Node.js。"
    exit 1
fi

# ─── Backend Setup ───────────────────────────────
echo "📦 配置后端..."
cd backend

# Create .env if not exists
if [ ! -f .env ]; then
    cp .env.example .env
    echo "⚠️  请编辑 backend/.env 文件，填入你的 OPENAI_API_KEY"
fi

# Create virtual environment
if [ ! -d venv ]; then
    python3 -m venv venv
fi

source venv/bin/activate
pip install -r requirements.txt -q

# Create directories
mkdir -p uploads data

echo "✅ 后端配置完成"

# ─── Frontend Setup ──────────────────────────────
echo "📦 配置前端..."
cd ../frontend

npm install -q

echo "✅ 前端配置完成"

# ─── Start Services ──────────────────────────────
echo ""
echo "🎯 启动服务..."
echo ""

# Start backend in background
cd ../backend
source venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload &
BACKEND_PID=$!
echo "✅ 后端已启动 (PID: $BACKEND_PID) → http://localhost:8000"
echo "   API 文档 → http://localhost:8000/docs"

# Start frontend in background
cd ../frontend
npm run dev &
FRONTEND_PID=$!
echo "✅ 前端已启动 (PID: $FRONTEND_PID) → http://localhost:3000"

echo ""
echo "========================================"
echo "  RAG 智能知识库已启动！"
echo "  前端: http://localhost:3000"
echo "  后端: http://localhost:8000"
echo "  API文档: http://localhost:8000/docs"
echo "========================================"
echo ""
echo "按 Ctrl+C 停止所有服务"

# Trap to kill background processes
trap "echo '停止服务...'; kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit" SIGINT SIGTERM

# Wait for background processes
wait
