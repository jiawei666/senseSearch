# GitHub OAuth 实施计划

基于设计文档 `docs/superpowers/specs/2026-04-19-github-oauth-design.md`

## 阶段概览

| Phase | 内容 | 依赖 |
|-------|------|------|
| Phase 1 | 后端 User 模型 + 配置 + 迁移 | 无 |
| Phase 2 | 后端 GitHub OAuth 服务层 + API 端点 | Phase 1 |
| Phase 3 | 后端测试 | Phase 2 |
| Phase 4 | 前端改动（删除注册、改造登录、新增 callback） | Phase 2 |
| Phase 5 | 前端测试 | Phase 4 |
| Phase 6 | 集成测试 + 提交 | Phase 3, 5 |

## Phase 1: 后端模型与配置

### 1.1 更新 config.py — 新增 GitHub OAuth 配置

文件: `backend/app/core/config.py`

新增字段:
```python
github_client_id: str = ""
github_client_secret: str = ""
github_redirect_uri: str = "http://localhost:8000/api/v1/auth/github/callback"
```

### 1.2 更新 User 模型

文件: `backend/app/models/user.py`

- 删除 `password_hash` 字段
- 新增 `github_id: Integer, unique, indexed`
- 新增 `avatar_url: String(500), nullable`
- `email` 改为 `nullable=True`

### 1.3 更新 .env.example 和 .env

文件: `backend/.env.example`, `backend/.env`

新增:
```
GITHUB_CLIENT_ID=your-github-client-id
GITHUB_CLIENT_SECRET=your-github-client-secret
GITHUB_REDIRECT_URI=http://localhost:8000/api/v1/auth/github/callback
```

## Phase 2: 后端 GitHub OAuth 服务层 + API

### 2.1 改造 services/auth.py

文件: `backend/app/services/auth.py`

- 删除 `verify_password()`, `get_password_hash()`
- 保留 `create_access_token()`, `decode_access_token()`
- 新增 `exchange_github_code(code: str) -> str` — POST https://github.com/login/oauth/access_token
- 新增 `get_github_user_info(access_token: str) -> dict` — GET https://api.github.com/user

使用 httpx.AsyncClient 调用 GitHub API。

### 2.2 改造 services/user.py

文件: `backend/app/services/user.py`

- 删除 `authenticate_user()`
- 保留 `get_user_by_id()`, `get_user_by_email()`
- 新增 `get_or_create_github_user(session, github_id, username, email, avatar_url) -> User`
  - 按 github_id 查找用户
  - 不存在则创建新用户
  - 存在则更新 username/avatar（GitHub 信息可能变化）

### 2.3 改造 schemas/auth.py

文件: `backend/app/schemas/auth.py`

- 删除 `RegisterRequest`, `LoginRequest`, `ErrorResponse`
- `UserResponse` 新增 `avatar_url: str | None`
- 保留 `TokenResponse`

### 2.4 改造 api/auth.py

文件: `backend/app/api/auth.py`

- 删除 `register` 和 `login` 端点
- 保留 `/me` 端点
- 新增 `GET /api/v1/auth/github` — 重定向到 GitHub 授权页
- 新增 `GET /api/v1/auth/github/callback` — 处理 GitHub 回调
  - 接收 `code` query param
  - 调用 `exchange_github_code` 换 access_token
  - 调用 `get_github_user_info` 获取用户信息
  - 调用 `get_or_create_github_user` 创建/查找本地用户
  - 签发 JWT
  - 重定向到前端 `http://localhost:3000/auth/callback?token={jwt}`
  - 错误时重定向到 `http://localhost:3000/auth/callback?error={error_type}`

## Phase 3: 后端测试

### 3.1 重写 tests/test_auth.py

文件: `backend/tests/test_auth.py`

TDD 方式编写测试:

1. **test_github_callback_creates_new_user** — Mock GitHub API 返回用户信息，验证新用户创建 + JWT 返回
2. **test_github_callback_finds_existing_user** — Mock GitHub API，验证已存在用户直接签发 JWT
3. **test_github_callback_updates_user_info** — 验证再次登录更新 avatar
4. **test_github_auth_url_redirects** — 验证 /auth/github 重定向到 GitHub
5. **test_github_callback_invalid_code** — Mock GitHub 返回错误，验证重定向到 error URL
6. **test_get_current_user** — 验证 /auth/me 端点
7. **test_get_current_user_invalid_token** — 验证 401 响应

使用 `unittest.mock.patch` mock httpx.AsyncClient。

## Phase 4: 前端改动

### 4.1 删除注册相关文件

- 删除 `frontend/app/register/page.tsx`
- 删除 `frontend/components/RegisterForm.tsx`
- 删除对应测试文件（如存在）

### 4.2 改造 lib/api/auth.ts

文件: `frontend/lib/api/auth.ts`

- 删除 `register()`, `login()` 方法
- 新增 `githubLogin()` — 跳转到后端 OAuth 入口
- 保留 `getCurrentUser()`, `logout()`, `isAuthenticated()`, `getToken()`

### 4.3 改造 app/login/page.tsx

文件: `frontend/app/login/page.tsx`

- 删除邮箱/密码表单
- 居中显示 "Sign in with GitHub" 按钮
- 点击调用 `githubLogin()`
- 保持复古科技感样式

### 4.4 新增 app/auth/callback/page.tsx

文件: `frontend/app/auth/callback/page.tsx`

'use client' 组件:
- useEffect 中从 URL searchParams 提取 token 或 error
- 有 token: 调用 `setAccessToken(token)`，router.push('/search')
- 有 error: 显示错误信息 + 重试链接
- 无 token/error: 显示加载状态

### 4.5 更新 API client 配置

文件: `frontend/lib/api/client.ts`

- 确认 `API_BASE_URL` 可用于 OAuth 跳转（可能需要从环境变量读取）

## Phase 5: 前端测试

### 5.1 更新 login 页面测试

验证 "Sign in with GitHub" 按钮存在，点击跳转正确 URL。

### 5.2 新增 callback 页面测试

验证 token 存储和跳转行为，验证错误场景显示。

### 5.3 更新 auth service 测试

删除 register/login 相关测试，新增 githubLogin 测试。

### 5.4 运行全部前端测试

确认 `npx vitest run` 全部通过。

## Phase 6: 集成与提交

### 6.1 运行后端全部测试

`cd backend && python -m pytest tests/ -v --tb=short`

### 6.2 运行前端全部测试

`cd frontend && npx vitest run`

### 6.3 手动验证流程

启动后端 + 前端，点击 GitHub 登录按钮，验证完整 OAuth 流程。

### 6.4 提交

```
feat: 替换注册登录为 GitHub OAuth 授权
```
