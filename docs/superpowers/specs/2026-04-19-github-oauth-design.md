# GitHub OAuth 认证设计

## 概述

将现有邮箱+密码注册/登录系统替换为 GitHub OAuth 授权登录。用户点击 "Sign in with GitHub" 按钮，跳转 GitHub 授权后自动创建本地账号并签发 JWT。

## 方案选择

采用标准 OAuth 2.0 Authorization Code Flow（方案 A），后端作为 OAuth client 处理 token 交换和用户创建，与现有 JWT 体系无缝对接。

## OAuth 流程

```
浏览器                     后端                      GitHub
  |-- 点击 "Sign in with GitHub"                    |
  |-- 重定向到 GitHub authorize_url                  |
  |<-- 用户授权页面 -------------------------------->|
  |-- 回调 /api/v1/auth/github/callback?code=xxx    |
  |----------------------->|-- POST /access_token -->|
  |                        |<-- access_token --------|
  |                        |-- GET /user ----------->|
  |                        |<-- {login, email, avatar}|
  |                        |                          |
  |                        |  创建/查找用户，签发 JWT  |
  |<-- 重定向 /auth/callback?token=jwt -------------|
  |                         |                          |
  |   前端存 JWT 到 localStorage                       |
  |   跳转 /search         |                          |
```

## 后端改动

### 新增配置项 (config.py)

| 配置项 | 说明 |
|--------|------|
| `GITHUB_CLIENT_ID` | GitHub OAuth App Client ID |
| `GITHUB_CLIENT_SECRET` | GitHub OAuth App Client Secret |
| `GITHUB_REDIRECT_URI` | 回调地址，如 `http://localhost:8000/api/v1/auth/github/callback` |

### User 模型变更 (models/user.py)

删除 `password_hash`，新增 `github_id` 和 `avatar_url`：

```python
class User:
    id: UUID                          # 主键
    github_id: Integer, unique        # GitHub user ID
    username: String(50), unique      # GitHub login
    email: String(255), nullable      # GitHub email（可能私有）
    avatar_url: String(500), nullable # GitHub avatar URL
    created_at: datetime
    updated_at: datetime
```

### Schema 变更 (schemas/auth.py)

- **删除**: `RegisterRequest`, `LoginRequest`
- **保留**: `TokenResponse`（不变），`UserResponse`（新增 `avatar_url` 字段）

### API 端点 (api/auth.py)

| 端点 | 方法 | 认证 | 说明 |
|------|------|------|------|
| `/api/v1/auth/github` | GET | 无 | 生成 GitHub 授权 URL 并 302 重定向 |
| `/api/v1/auth/github/callback` | GET | 无 | 接收 code，换 token，创建/查找用户，签发 JWT，重定向到前端 |
| `/api/v1/auth/me` | GET | JWT | 获取当前用户（不变） |

**删除端点**: `POST /api/v1/auth/register`, `POST /api/v1/auth/login`

### 服务层变更 (services/)

- **auth.py**: 删除 `verify_password`、`get_password_hash`，保留 `create_access_token`、`decode_access_token`。新增 `exchange_github_code(code)` 和 `get_github_user_info(access_token)` 使用 httpx 调用 GitHub API。
- **user.py**: 删除 `authenticate_user`。新增 `get_or_create_github_user(session, github_id, username, email, avatar_url)` — 按 `github_id` 查找，不存在则创建。

### 错误处理

| 场景 | 状态码 | 处理 |
|------|--------|------|
| GitHub token 交换失败 | 401 | 重定向前端 `/auth/callback?error=github_auth_failed` |
| GitHub API 获取用户失败 | 502 | 重定向前端 `/auth/callback?error=github_api_error` |
| GitHub email 私有 | - | email 允许为 null，不阻断流程 |
| JWT 无效/过期 | 401 | 现有逻辑不变 |

## 前端改动

### 删除文件

- `app/register/page.tsx` — 注册页
- `components/RegisterForm.tsx` — 注册表单组件

### 改造 app/login/page.tsx

- 去掉邮箱/密码表单
- 单个 "Sign in with GitHub" 按钮 + GitHub icon
- 点击跳转 `${API_BASE_URL}/api/v1/auth/github`
- 保持复古科技感样式（浅米色底 + 纯黑文字 + 等宽字体）

### 新增 app/auth/callback/page.tsx

- 从 URL query param 提取 `token`
- 调用 `setAccessToken(token)` 存储 JWT
- 跳转到 `/search`
- 处理错误：`error` query param 时显示错误提示，提供重试链接

### 改造 lib/api/auth.ts

- **删除**: `register()`、`login()` 方法
- **新增**: `githubLogin()` — `window.location.href = ${API_BASE_URL}/api/v1/auth/github`
- **保留**: `getCurrentUser()`、`logout()`、`isAuthenticated()`、`getToken()`

## 测试策略

### 后端测试

替换 `tests/test_auth.py`，使用 mock 测试：

- Mock `httpx.AsyncClient` 调用 GitHub token 和 user API
- 测试首次登录自动创建用户
- 测试再次登录查找已有用户
- 测试 JWT 签发和 `/auth/me` 端点
- 测试错误场景（GitHub 返回错误、code 无效）

### 前端测试

- 更新 login 页面测试 — 验证 GitHub 按钮存在且点击跳转正确 URL
- 新增 auth/callback 页面测试 — 验证 token 存储和跳转行为
- 删除 RegisterForm 相关测试
- 删除 `authService.register` 和 `authService.login` 相关测试

## 数据库迁移

Alembic migration：

- 删除 `users.password_hash` 列
- 新增 `users.github_id` 列 (Integer, unique, indexed)
- 新增 `users.avatar_url` 列 (String(500), nullable)
- `users.email` 改为 nullable

现有用户数据不迁移（认证体系完全不同）。

## 依赖变化

### 后端

无新增依赖。`httpx` 已在项目中用于调用 GitHub API。删除 `passlib`、`bcrypt` 相关代码（不再需要密码哈希）。

### 前端

无新增依赖。

## 前置条件

用户需要在 GitHub 上创建 OAuth App：

1. 访问 https://github.com/settings/developers → New OAuth App
2. Application name: `SenseSearch`
3. Homepage URL: `http://localhost:3000`
4. Authorization callback URL: `http://localhost:8000/api/v1/auth/github/callback`
5. 获取 Client ID 和 Client Secret，配置到后端 `.env`
