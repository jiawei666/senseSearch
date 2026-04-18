# SenseSearch - 多模态对话式搜索引擎设计文档

> 日期: 2026-04-18
> 状态: 已批准
> 开发模式: TDD（测试驱动开发）

## 1. 产品定位

**SenseSearch** 是一个面向 C 端用户的对话式多模态搜索引擎。用户可以通过文字、图片或视频进行搜索，AI 助手理解意图并返回跨模态匹配结果。

**核心价值：** 全模态互搜（文本/图片/视频任意组合）+ 对话式交互（意图理解、追问澄清、结果总结）。

## 2. 产品形态

- **第一版：** Web 应用（Next.js 前端 + FastAPI 后端）
- **内容来源：** 私有 + 公共混合（用户上传 + 平台预置种子数据）
- **用户：** C 端普通用户，需注册登录（公共内容可浏览）

### 2.1 用户流程

```
用户进入首页
  ├─ 输入文字描述 → 搜索匹配的图片/视频
  ├─ 上传/拖拽图片 → 搜索相似图片或相关视频
  ├─ 上传视频片段 → 搜索相关内容
  └─ 多轮对话 → AI 追问澄清意图 → 精准搜索 → 总结结果
```

### 2.2 UI 设计方向

参考 mails.dev 的极简主义 + 复古科技感风格：

| 维度 | 决策 |
|------|------|
| 视觉风格 | 极简主义 + 复古科技感 |
| 配色 | 浅米色底 (#F5F5F5) + 纯黑文字/按钮 (#000000) + 低饱和莫兰迪色系 |
| 字体 | 粗体无衬线标题 + 等宽字体代码元素 |
| 布局 | 模块化水平分割，左右分栏 |
| 首页 | 左侧功能区（搜索框 + 热门标签）+ 右侧视觉插画区 |
| 搜索结果页 | 左侧 AI 对话流 + 右侧结果卡片网格 |
| 交互 | 功能优先，hover 状态反馈，输入框聚焦边框变深 |

## 3. 架构方案

**选定方案：统一嵌入空间 + LLM 对话编排**

用一个多模态嵌入模型将文本、图片、视频帧统一映射到同一向量空间，所有模态共享一个 Milvus collection。LLM 作为对话层，理解用户意图、组装查询、总结结果。

**优势：** 架构简洁、跨模态搜索天然支持、开发周期短。

```
┌──────────────────────────────────────────────────┐
│                   Frontend (Next.js)             │
│         对话界面 + 搜索结果展示 + 内容上传        │
└──────────────────────┬──────────────────────────┘
                       │ REST API / SSE
┌──────────────────────▼──────────────────────────┐
│                Backend (FastAPI)                  │
│                                                   │
│  ┌──────────┐  ┌──────────┐  ┌───────────────┐  │
│  │ 对话引擎  │  │ 搜索引擎  │  │ 索引管线      │  │
│  │ (LLM)    │  │ (Milvus) │  │ (嵌入+入库)   │  │
│  └──────────┘  └──────────┘  └───────────────┘  │
│                                                   │
│  ┌──────────┐  ┌──────────┐  ┌───────────────┐  │
│  │ 文件服务  │  │ 内容管理  │  │ 用户服务      │  │
│  │ (存储)   │  │ (元数据) │  │ (认证/权限)   │  │
│  └──────────┘  └──────────┘  └───────────────┘  │
└──────────┬───────────┬──────────────┬───────────┘
           │           │              │
     ┌─────▼──┐  ┌─────▼─────┐  ┌────▼────┐
     │ Milvus │  │ PostgreSQL │  │  本地    │
     │ (向量)  │  │ (元数据)   │  │  存储    │
     └────────┘  └───────────┘  └─────────┘
```

### 3.1 六个核心模块

| 模块 | 职责 | 关键依赖 |
|------|------|----------|
| 对话引擎 | 意图识别、多轮对话、结果总结 | 国内大模型 API（通义千问等） |
| 搜索引擎 | 向量相似度搜索、结果排序 | Milvus (milvus-lite) |
| 索引管线 | 多模态嵌入、视频抽帧、数据入库 | 国内多模态嵌入 API |
| 文件服务 | 文件上传、存储、缩略图生成 | 本地文件系统 |
| 内容管理 | 内容元数据 CRUD、标签、权限 | PostgreSQL |
| 用户服务 | 注册登录、权限、个人库隔离 | JWT |

## 4. 技术栈

| 层 | 技术 | 说明 |
|----|------|------|
| 前端 | Next.js 14+ (App Router) | React 生态，SSR 支持 |
| 后端 | FastAPI (Python 3.11+) | 异步，自动 API 文档 |
| 向量数据库 | Milvus Lite | 单机嵌入式，无需独立服务 |
| 关系数据库 | PostgreSQL | 元数据、用户、对话记录 |
| 文件存储 | 本地文件系统 (MVP) | 后续可切换 OSS |
| 嵌入 API | 国内多模态嵌入 API | 文本+图片统一向量空间 |
| LLM API | 国内大模型 API | 对话理解、意图识别、结果总结 |
| 视频处理 | ffmpeg + OpenCV | 抽帧、关键帧提取 |

## 5. 数据模型

### 5.1 PostgreSQL 表结构

**users 表：**
- id: UUID PK
- email: string UNIQUE NOT NULL
- password_hash: string NOT NULL
- display_name: string
- created_at: datetime

**content 表：**
- id: UUID PK
- type: enum(text, image, video) NOT NULL
- title: string
- description: text
- file_path: string
- source: enum(public, private) NOT NULL
- owner_id: UUID FK → users (私有内容的归属用户)
- tags: string[]
- status: enum(pending, indexed, index_failed) DEFAULT pending
- created_at: datetime
- metadata: jsonb (帧时间戳、分辨率、文件大小等)

**conversations 表：**
- id: UUID PK
- user_id: UUID FK → users
- title: string
- created_at: datetime
- updated_at: datetime

**messages 表：**
- id: UUID PK
- conversation_id: UUID FK → conversations
- role: enum(user, assistant) NOT NULL
- content: text NOT NULL
- attachments: jsonb (上传的图片/视频引用)
- search_results: jsonb (AI 搜索结果引用)
- created_at: datetime

### 5.2 Milvus Collection

Collection 名称: `content_embeddings`

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INT64 (auto) | Milvus 内部 ID |
| content_id | VARCHAR | 关联 content 表 UUID |
| embedding | FLOAT_VECTOR(512) | 嵌入向量（维度取决于模型） |
| modality | VARCHAR | text / image / video_frame |
| frame_index | INT32 | 视频帧序号，非视频为 -1 |

- 索引: IVF_FLAT，nlist=128
- 距离度量: COSINE

## 6. 核心工作流

### 6.1 搜索工作流

```
用户输入（文字/图片/视频）
       │
       ▼
  文件预处理
  图片：压缩 → 嵌入
  视频：ffmpeg抽帧 → 逐帧嵌入
       │  query_vector(s)
       ▼
  对话引擎 LLM
  理解意图 → 决定搜索策略
       │
       ▼
  Milvus 搜索
  top_k=20, cosine similarity
       │  raw_results
       ▼
  结果后处理
  去重（同视频多帧合并）→ 关联元数据 → 排序
       │
       ▼
  LLM 总结
  描述搜索结果 → 生成自然语言回答
       │
       ▼
  返回前端（对话消息 + 结果卡片）
```

### 6.2 索引工作流

```
文件上传
    │
    ├── 图片 → 调用嵌入 API → 向量写入 Milvus + 元数据写入 PG
    │
    ├── 视频 → ffmpeg 每 2 秒抽帧 → 批量嵌入 → 批量写入 Milvus + 元数据写入 PG
    │
    └── 纯文本 → 调用文本嵌入 API → 向量写入 Milvus + 元数据写入 PG
```

### 6.3 LLM Prompt 策略

系统提示词核心逻辑：

1. 理解用户搜索意图
2. 意图不明确时追问澄清（最多 2 轮）
3. 意图明确后返回结构化搜索指令
4. 收到搜索结果后用自然语言总结并引用结果

输出格式：
- 需要搜索: `{ "action": "search", "query": "...", "filters": {...} }`
- 需要追问: `{ "action": "clarify", "question": "..." }`
- 总结结果: `{ "action": "summarize", "answer": "...", "result_ids": [...] }`

## 7. API 设计

```
POST   /api/v1/search              — 搜索（支持文字/图片/视频查询）
POST   /api/v1/search/stream       — 流式搜索（SSE，逐步返回结果）

POST   /api/v1/content/upload      — 上传内容（图片/视频）
GET    /api/v1/content/{id}        — 获取内容详情
DELETE /api/v1/content/{id}        — 删除内容
GET    /api/v1/content             — 列出用户的内容库

POST   /api/v1/conversations       — 创建对话
GET    /api/v1/conversations/{id}  — 获取对话历史
POST   /api/v1/conversations/{id}/messages — 发送消息（搜索触发点）

POST   /api/v1/auth/register       — 注册
POST   /api/v1/auth/login          — 登录
GET    /api/v1/auth/me             — 当前用户信息
```

## 8. 错误处理

| 场景 | 处理策略 |
|------|----------|
| 嵌入 API 超时/失败 | 重试 1 次 → 降级返回"搜索暂时不可用" |
| Milvus 查询失败 | 重试 1 次 → 降级到 PostgreSQL 全文搜索（纯文本场景） |
| 视频抽帧失败 | 记录失败日志 → 标记内容为 index_failed → 通知用户重新上传 |
| 文件过大/格式不支持 | 上传时前端校验 + 后端二次校验 → 返回明确错误信息 |
| LLM API 失败 | 重试 1 次 → 跳过对话总结，直接返回原始搜索结果 |
| 用户未登录 | 前端拦截 → 跳转登录页（公共内容可浏览，上传/私有库需登录） |

## 9. 测试策略

**开发模式：TDD（测试驱动开发）**

强制工作流：
1. 写测试先 (RED)
2. 写最小实现 (GREEN)
3. 重构 (IMPROVE)
4. 验证覆盖率 >= 80%

| 类型 | 范围 | 工具 |
|------|------|------|
| 单元测试 | 嵌入管线、搜索逻辑、数据模型、API 端点 | pytest + httpx |
| 集成测试 | 完整搜索链路（上传 → 索引 → 搜索 → 返回） | pytest + milvus-lite test fixture |
| E2E 测试 | 用户核心流程（注册 → 上传 → 搜索 → 对话） | Playwright |
| API 契约测试 | 前后端接口一致性 | OpenAPI schema 校验 |

## 10. 部署架构（MVP 单机）

```
单台服务器 (4C8G)
├── Docker Compose
│   ├── web (Next.js)        — 端口 3000
│   ├── api (FastAPI)        — 端口 8000
│   ├── postgres              — 端口 5432
│   └── nginx                 — 端口 80/443，反向代理
├── Milvus Lite              — 嵌入式，无需独立进程
└── 本地文件存储               — /data/uploads/
```

## 11. MVP 范围

### 做（V1）

- 文字搜索图片/视频
- 图片搜索图片/视频
- 视频搜索图片/视频
- 对话式搜索（多轮澄清 + 结果总结）
- 用户注册登录（JWT）
- 私有内容上传和索引
- 公共内容库（预置种子数据）
- 极简复古科技感 UI

### 不做（V1）

- 视频内容语义理解（只做帧级搜索）
- 内容标签自动生成
- 个性化推荐
- 多语言（先做中文）
- 移动端原生 App
- 付费体系
- OSS 云存储
