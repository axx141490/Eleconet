"""User subscription tier limits."""

from dataclasses import dataclass
from typing import Set


@dataclass(frozen=True)
class TierLimits:
    max_knowledge_bases: int        # 知识库数量上限
    max_docs_per_kb: int            # 单知识库文档数上限
    max_file_size_mb: int           # 单文件大小限制 (MB)
    allowed_file_types: Set[str]    # None = all types allowed
    can_share: bool                 # 分享链接权限
    max_conversations: int          # 对话历史保留数量


# "基础" formats for Free tier: text, pdf, docx
BASIC_FILE_TYPES: Set[str] = {"text", "pdf", "docx"}
ALL_FILE_TYPES: Set[str] = {"text", "pdf", "docx", "xlsx", "pptx", "image", "audio", "video"}

BASIC_EXTENSIONS: Set[str] = {
    ".txt", ".md", ".csv", ".json", ".log", ".xml", ".yaml", ".yml",
    ".pdf",
    ".docx", ".doc",
}

TIER_LIMITS = {
    "free": TierLimits(
        max_knowledge_bases=5,
        max_docs_per_kb=10,
        max_file_size_mb=1,
        allowed_file_types=BASIC_FILE_TYPES,
        can_share=False,
        max_conversations=10,
    ),
    "pro": TierLimits(
        max_knowledge_bases=100,
        max_docs_per_kb=100,
        max_file_size_mb=1024,  # 1 GB
        allowed_file_types=ALL_FILE_TYPES,
        can_share=True,
        max_conversations=100,
    ),
    "enterprise": TierLimits(
        max_knowledge_bases=100,
        max_docs_per_kb=1000,
        max_file_size_mb=1024,  # 1 GB
        allowed_file_types=ALL_FILE_TYPES,
        can_share=True,
        max_conversations=1000,
    ),
}

TIER_DISPLAY = {
    "free": "Free",
    "pro": "Pro",
    "enterprise": "Enterprise",
}


def get_tier_limits(tier: str) -> TierLimits:
    return TIER_LIMITS.get(tier, TIER_LIMITS["free"])
