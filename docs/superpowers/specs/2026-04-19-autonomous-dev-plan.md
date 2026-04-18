# SenseSearch - 自主开发执行计划

> 日期: 2026-04-19
> 状态: 已批准
> 模式: Loop (20分钟/轮) + Teams (3 agents)
> 分支: main 直接开发

## 1. 团队结构

```
Lead (主控)
├── backend — FastAPI 后端开发
├── frontend — Next.js 前端开发
└── tester — E2E 测试 + 集成测试
```

## 2. 开发阶段

### Phase 1: 基础设施（并行，无外部依赖）

**backend:**
- 初始化 FastAPI 项目结构
- 配置 PostgreSQL 数据模型 (SQLAlchemy)
- 配置 Milvus Lite 连接
- 基础配置管理 (pydantic-settings)

**frontend:**
- 初始化 Next.js 项目 (App Router)
- 页面路由：首页、搜索结果页、登录/注册
- 基础 UI 组件库（搜索框、卡片、对话气泡）
- 复古科技感主题配置

### Phase 2: 核心后端（串行，TDD）

按依赖顺序：
1. 用户服务 (auth) — 注册/登录/JWT — TDD
2. 文件服务 (upload/storage) — 文件上传/存储/缩略图 — TDD
3. 索引管线 (embedding) — 多模态嵌入 + Milvus 写入 — TDD
4. 搜索引擎 (search) — Milvus 查询 + 结果后处理 — TDD
5. 对话引擎 (conversation) — LLM 意图理解 + 结果总结 — TDD

### Phase 3: 前端对接（依赖 Phase 2）

1. 搜索页面 + 对话组件（对接 /api/v1/search/stream）
2. 上传交互（对接 /api/v1/content/upload）
3. 结果卡片展示（图片网格 + 视频预览）
4. 登录/注册页面对接

### Phase 4: 集成与部署

1. tester: 全链路 E2E 测试
2. Docker Compose 配置
3. Nginx 反向代理配置
4. 种子数据导入

## 3. Loop 工作流程

每 20 分钟一轮：
1. 读取 TaskList，检查进度
2. 给空闲 agent 分配新任务
3. 审阅已完成任务的代码
4. 处理 agent 报告的阻塞问题
5. 每完成一个 Phase 自动 commit + push
6. 无法解决的问题 → 暂停并记录

## 4. TDD 强制规则

- 写测试先 (RED) → 实现 (GREEN) → 重构 (IMPROVE)
- 测试不通过 = 任务未完成
- 覆盖率目标 >= 80%
- 后端: pytest + httpx
- 前端: vitest + testing-library
- E2E: playwright

## 5. 安全机制

- Phase 完成后 commit + push，防中断丢进度
- agent 连续 3 次失败 → 暂停该任务
- API key 通过 .env 注入，不硬编码
- .gitignore 排除 .env, node_modules, __pycache__, .milvus 等

## 6. 技术栈参考

详见主设计文档: [2026-04-18-sensesearch-design.md](./2026-04-18-sensesearch-design.md)
