# RAG 技术架构说明

## 一、系统概述

本系统采用 **Naive RAG** 架构，实现"文档解析 → 分块 → 向量化 → 检索 → 生成"的标准流程，为用户提供基于私有知识库的智能问答能力。

```
用户提问
   │
   ▼
查询向量化（Embedding）
   │
   ▼
向量检索（ChromaDB / 余弦相似度）
   │
   ▼
上下文构建（Top-K 召回 + 相关度标注）
   │
   ▼
LLM 生成（多轮对话 + 来源引用）
   │
   ▼
返回答案 + 来源文档
```

---

## 二、核心技术组件

### 2.1 文档解析

支持多种文件格式的解析，统一提取纯文本后进入处理流程：

| 格式 | 解析方式 |
|------|---------|
| PDF | pdfplumber + 百度 OCR（扫描件） |
| Word (.docx) | python-docx |
| Excel (.xlsx) | openpyxl |
| PowerPoint (.pptx) | python-pptx |
| 图片 | 百度 OCR |
| 音频/视频 | Whisper 语音转文字 |
| TXT / Markdown | 直接读取 |

### 2.2 文本分块（Chunking）

**策略：段落优先 + 句子级回退 + 滑动窗口重叠**

```
默认参数：
  chunk_size    = 1000 字符
  chunk_overlap = 200  字符
```

分块逻辑分三层：

1. **段落分割**：以双换行（`\n\n`）为边界切分
2. **句子分割**：单段落超过 chunk_size 时，按句号/问号/感叹号切分
3. **硬切分**：单句仍超长时，按字符数强制截断

重叠窗口（overlap）保留上下文连续性，避免语义在块边界断裂。

**工程参考：**
> LangChain. *RecursiveCharacterTextSplitter*. 官方文档：https://python.langchain.com（搜索 RecursiveCharacterTextSplitter）

### 2.3 向量嵌入（Embedding）

使用 OpenAI Embedding API 将文本块转为稠密向量：

```
默认模型：text-embedding-3-small
向量维度：1536
```

**对应论文：**
> Neelakantan et al. (2022). *Text and Code Embeddings by Contrastive Pre-Training*. OpenAI Technical Report. https://arxiv.org/abs/2201.10005

### 2.4 向量存储与检索

使用 **ChromaDB** 作为向量数据库，采用余弦相似度 + HNSW 索引：

```python
metadata={"hnsw:space": "cosine"}
```

检索流程：
1. 将用户问题向量化
2. 在对应知识库 Collection 中查询 Top-K 最相似块（默认 K=5）
3. 返回文本、元数据及相关度分数（`relevance_score = 1 - cosine_distance`）

**对应论文：**
> Malkov & Yashunin (2018). *Efficient and Robust Approximate Nearest Neighbor Search Using Hierarchical Navigable Small World Graphs*. IEEE TPAMI. https://arxiv.org/abs/1603.09320
>
> Johnson et al. (2019). *Billion-scale similarity search with GPUs*. IEEE TPAMI. https://arxiv.org/abs/1702.08734

### 2.5 上下文构建与提示工程

检索到的 Top-K 块按如下格式拼接为上下文，注入 System Prompt：

```
[Document 1] (Relevance: 0.87)
<chunk text>

---

[Document 2] (Relevance: 0.81)
<chunk text>
```

System Prompt 核心规则：
- 仅依据上下文回答，不编造信息
- 使用 `[Document N]` 标注来源
- 自动匹配用户语言（中文/英文）

### 2.6 多轮对话

保留最近 **3 轮**（6 条消息）的历史注入到 messages 列表，实现上下文连贯的多轮问答。

**对应论文：**
> OpenAI (2022). *ChatGPT: Optimizing Language Models for Dialogue*.

### 2.7 生成（LLM）

支持多种 LLM 后端，兼容 OpenAI API 协议：

```
默认模型：gpt-4o-mini
temperature：0.7（可配置）
max_tokens：2000
```

支持**流式输出**（SSE），提升用户响应体验。

---

## 三、奠基论文

| 论文 | 贡献 |
|------|------|
| 论文 | 贡献 | 链接 |
|------|------|------|
| Lewis et al. (2020). *Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks*. NeurIPS 2020. | RAG 范式的奠基论文，提出 Retriever + Generator 联合框架 | https://arxiv.org/abs/2005.11401 |
| Malkov & Yashunin (2018). *Efficient and Robust Approximate Nearest Neighbor Search Using HNSW*. IEEE TPAMI. | 当前系统向量索引（HNSW）的理论基础 | https://arxiv.org/abs/1603.09320 |
| Neelakantan et al. (2022). *Text and Code Embeddings by Contrastive Pre-Training*. OpenAI. | `text-embedding-3-small` 所属系列论文 | https://arxiv.org/abs/2201.10005 |
| Johnson et al. (2019). *Billion-scale Similarity Search with GPUs (FAISS)*. IEEE TPAMI. | 大规模向量检索的工程基础 | https://arxiv.org/abs/1702.08734 |
| Robertson & Zaragoza (2009). *The Probabilistic Relevance Framework: BM25 and Beyond*. | 稀疏检索基准，混合检索的对比参照 | — |

---

## 四、当前架构局限与升级路径

当前系统为 Naive RAG，后续可按需引入以下进阶技术：

| 问题 | 进阶技术 | 参考论文 |
|------|---------|---------|
| 问题 | 进阶技术 | 参考论文 | 链接 |
|------|---------|---------|------|
| 用户提问表达不精确，召回质量差 | **HyDE**（假设文档嵌入） | Gao et al. (2022). *Precise Zero-Shot Dense Retrieval without Relevance Labels*. | https://arxiv.org/abs/2212.10496 |
| 召回块排序不够准确 | **Reranker**（交叉编码器重排序） | Nogueira et al. (2019). *Passage Re-ranking with BERT*. | https://arxiv.org/abs/1901.04085 |
| 纯向量检索遗漏关键词匹配 | **混合检索**（BM25 + 向量） | Robertson & Zaragoza (2009). *The Probabilistic Relevance Framework: BM25 and Beyond*. | — |
| 复杂关系推理能力弱 | **GraphRAG** | Edge et al. (2024). *From Local to Global: A Graph RAG Approach*. Microsoft Research. | https://arxiv.org/abs/2404.16130 |
| 多跳问题（需跨文档推理） | **Multi-hop RAG** | Yang et al. (2018). *HotpotQA: A Dataset for Diverse, Explainable Multi-hop Question Answering*. | https://arxiv.org/abs/1809.09600 |

---

## 五、系统参数配置

| 参数 | 默认值 | 说明 |
|------|-------|------|
| `CHUNK_SIZE` | 1000 | 每块最大字符数 |
| `CHUNK_OVERLAP` | 200 | 块间重叠字符数 |
| `top_k` | 5 | 每次检索返回的最相关块数 |
| `temperature` | 0.7 | 生成温度，越低越保守 |
| `max_tokens` | 2000 | 单次生成最大 token 数 |
| `OPENAI_EMBEDDING_MODEL` | text-embedding-3-small | 向量化模型 |
| `OPENAI_CHAT_MODEL` | gpt-4o-mini | 对话生成模型 |
