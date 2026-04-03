"""Pydantic schemas for API request/response validation."""

import re
from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import List, Optional
from datetime import datetime

def validate_password_strength(v: str) -> str:
    errors = []
    if len(v) < 8:
        errors.append("至少 8 位")
    if not re.search(r'[A-Z]', v):
        errors.append("至少一个大写字母")
    if not re.search(r'[a-z]', v):
        errors.append("至少一个小写字母")
    if not re.search(r'\d', v):
        errors.append("至少一个数字")
    if not re.search(r'[!@#$%^&*()\-_=+\[\]{};:\'",.<>?/\\|`~]', v):
        errors.append("至少一个特殊符号（如 !@#$%^&*）")
    if errors:
        raise ValueError("密码需满足：" + "、".join(errors))
    return v


# ─── Auth Schemas ───────────────────────────────────────────
class UserRegister(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: str = Field(..., max_length=100)
    password: str = Field(..., min_length=8)
    phone: Optional[str] = Field(None, max_length=20)
    sms_code: Optional[str] = Field(None, max_length=6)

    @field_validator("password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        return validate_password_strength(v)


class UserLogin(BaseModel):
    username: str
    password: str


class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    phone: Optional[str] = None
    is_active: bool
    is_admin: bool
    role: str = "user"
    tier: str = "free"
    tier_expires_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


# ─── Knowledge Base Schemas ─────────────────────────────────
class KBCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    description: str = Field(default="", max_length=1000)


class KBUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)


class KBResponse(BaseModel):
    id: int
    name: str
    description: str
    document_count: int
    total_chunks: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class DocumentResponse(BaseModel):
    id: int
    filename: str
    file_type: str
    file_size: int
    status: str
    chunk_count: int
    error_message: Optional[str]
    created_at: datetime
    processed_at: Optional[datetime]

    class Config:
        from_attributes = True


class KBDetailResponse(KBResponse):
    documents: List[DocumentResponse] = []


# ─── Chat Schemas ───────────────────────────────────────────
class ChatRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=5000)
    kb_id: int
    conversation_id: Optional[int] = None
    top_k: int = Field(default=5, ge=1, le=20)
    temperature: float = Field(default=0.7, ge=0, le=2)


class SourceInfo(BaseModel):
    document: str
    relevance_score: float
    file_type: str


class ChatResponse(BaseModel):
    answer: str
    sources: List[SourceInfo]
    conversation_id: int
    message_id: int


# ─── Conversation Schemas ───────────────────────────────────
class ConversationResponse(BaseModel):
    id: int
    title: str
    kb_id: Optional[int]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class MessageResponse(BaseModel):
    id: int
    role: str
    content: str
    sources: Optional[List[dict]]
    created_at: datetime

    class Config:
        from_attributes = True


class ConversationDetailResponse(ConversationResponse):
    messages: List[MessageResponse] = []


# ─── Stats Schemas ──────────────────────────────────────────
class SystemStats(BaseModel):
    total_users: int
    total_knowledge_bases: int
    total_documents: int
    total_conversations: int
    supported_formats: List[str]
