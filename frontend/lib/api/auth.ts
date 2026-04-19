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
 * 注册请求接口
 */
export interface RegisterRequest {
  username: string
  email: string
  password: string
}

/**
 * 登录响应接口
 */
export interface LoginResponse {
  accessToken: string
}

/**
 * Auth 服务
 */
export const authService = {
  /**
   * 用户注册
   */
  async register(data: RegisterRequest): Promise<User> {
    try {
      const response = await apiClient.post<User>('/api/v1/auth/register', data)
      return response
    } catch (error) {
      if (error instanceof ApiError) {
        throw new Error(error.data?.detail || '注册失败')
      }
      throw error
    }
  },

  /**
   * 用户登录
   */
  async login(email: string, password: string): Promise<LoginResponse> {
    try {
      const response = await apiClient.post<{
        access_token: string
        token_type: string
      }>('/api/v1/auth/login', {
        email,
        password,
      })

      const { access_token } = response
      setAccessToken(access_token)

      return { accessToken: access_token }
    } catch (error) {
      if (error instanceof ApiError) {
        throw new Error(error.data?.detail || '登录失败')
      }
      throw error
    }
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
