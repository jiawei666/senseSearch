/**
 * Auth API 服务 - 处理认证相关操作
 */
import { apiClient, getAccessToken, setAccessToken, clearAccessToken, ApiError } from './client'

/**
 * 用户信息接口
 */
export interface User {
  id: string
  username: string
  email: string
}

/**
 * Auth 服务
 */
export const authService = {
  /**
   * GitHub OAuth 登录
   * 重定向到后端的 GitHub OAuth 授权端点
   */
  githubLogin(): void {
    const apiBaseUrl =
      process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000'
    window.location.href = `${apiBaseUrl}/api/v1/auth/github`
  },

  /**
   * 获取当前用户信息
   */
  async getCurrentUser(): Promise<User> {
    try {
      const response = await apiClient.get<User>('/api/v1/auth/me')
      return response
    } catch (error) {
      if (error instanceof ApiError && error.status === 401) {
        // 401 表示未登录，清除 token
        clearAccessToken()
        throw new Error('请先登录')
      }
      if (error instanceof ApiError) {
        throw new Error(error.data?.detail || '获取用户信息失败')
      }
      throw error
    }
  },

  /**
   * 登出
   */
  logout(): void {
    clearAccessToken()
    // 触发登出事件
    if (typeof window !== 'undefined') {
      window.dispatchEvent(new CustomEvent('auth:logout'))
    }
  },

  /**
   * 检查是否已登录
   */
  isAuthenticated(): boolean {
    const token = getAccessToken()
    return token !== null && token !== undefined && token.length > 0
  },

  /**
   * 获取当前 token
   */
  getToken(): string | null {
    return getAccessToken()
  },
}

// 导出 token 管理函数供外部使用
export { setAccessToken, clearAccessToken, getAccessToken }
