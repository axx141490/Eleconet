"""FastAPI application entry point."""

import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.core.config import get_settings
from app.core.database import init_db
from app.api.auth import router as auth_router
from app.api.knowledge_base import router as kb_router
from app.api.chat import router as chat_router
from app.api.stats import router as stats_router
from app.api.settings import router as settings_router
from app.api.share import router as share_router
from app.api.admin import router as admin_router
from app.api.guest import router as guest_router
from app.api.payment import router as payment_router
from app.api.kb_market import router as market_router

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown events."""
    # Startup
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    os.makedirs(settings.CHROMA_PERSIST_DIR, exist_ok=True)
    os.makedirs("./data", exist_ok=True)
    await init_db()
    print(f"✅ {settings.APP_NAME} started on {settings.APP_HOST}:{settings.APP_PORT}")
    yield
    # Shutdown
    print("👋 Application shutting down...")


app = FastAPI(
    title=settings.APP_NAME,
    description="Multi-format RAG Knowledge Base with Intelligent Q&A",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://eleconet.cn", "https://www.eleconet.cn", "http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth_router)
app.include_router(kb_router)
app.include_router(chat_router)
app.include_router(stats_router)
app.include_router(settings_router)
app.include_router(share_router)
app.include_router(admin_router)
app.include_router(guest_router)
app.include_router(payment_router)
app.include_router(market_router)


@app.get("/api/health")
async def health_check():
    return {
        "status": "healthy",
        "app": settings.APP_NAME,
        "version": "1.0.0",
    }


@app.get("/api/supported-formats")
async def get_supported_formats():
    from app.parsers import ParserFactory
    return {
        "formats": ParserFactory.get_supported_extensions(),
        "categories": {
            "text": [".txt", ".md", ".csv", ".json", ".log", ".xml", ".yaml", ".yml"],
            "pdf": [".pdf"],
            "word": [".docx", ".doc"],
            "excel": [".xlsx", ".xls"],
            "powerpoint": [".pptx", ".ppt"],
            "image": [".png", ".jpg", ".jpeg", ".gif", ".bmp", ".webp"],
            "audio": [".mp3", ".wav", ".m4a", ".ogg", ".flac"],
            "video": [".mp4", ".avi", ".mkv", ".mov", ".wmv", ".webm"],
        }
    }
