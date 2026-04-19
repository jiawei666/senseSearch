import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest'
import { authService, setAccessToken, clearAccessToken, getAccessToken } from '../auth'
import { apiClient, __resetMemoryTokenForTesting } from '../client'

vi.mock('../client', async (importOriginal) => {
  const actual = await importOriginal<typeof import('../client')>()
  // 只 mock apiClient，保留真实的 token 管理函数
  return {
    ...actual,
    apiClient: {
      get: vi.fn(),
      post: vi.fn(),
      put: vi.fn(),
      delete: vi.fn(),
      upload: vi.fn(),
    },
  }
})

describe('authService', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    clearAccessToken()
    __resetMemoryTokenForTesting()
  })

  const mockUser = {
    id: '1',
    username: 'testuser',
    email: 'test@example.com',
  }

  const mockToken = 'test-access-token'

  describe('register', () => {
    it('应该发送注册请求', async () => {
      vi.mocked(apiClient.post).mockResolvedValueOnce(mockUser)

      const result = await authService.register({
        username: 'testuser',
        email: 'test@example.com',
        password: 'Password123',
      })

      expect(apiClient.post).toHaveBeenCalledWith('/api/v1/auth/register', {
        username: 'testuser',
        email: 'test@example.com',
        password: 'Password123',
      })
      expect(result).toEqual(mockUser)
    })

    it('应该处理注册错误', async () => {
      const error = new Error('用户已存在')
      vi.mocked(apiClient.post).mockRejectedValueOnce(error)

      await expect(
        authService.register({
          username: 'testuser',
          email: 'test@example.com',
          password: 'Password123',
        })
      ).rejects.toThrow('用户已存在')
    })
  })

  describe('login', () => {
    it('应该发送登录请求并保存 token', async () => {
      vi.mocked(apiClient.post).mockResolvedValueOnce({
        access_token: mockToken,
        token_type: 'bearer',
      })

      const result = await authService.login('test@example.com', 'Password123')

      expect(apiClient.post).toHaveBeenCalledWith('/api/v1/auth/login', {
        email: 'test@example.com',
        password: 'Password123',
      })
      expect(result).toEqual({ accessToken: mockToken })
      expect(getAccessToken()).toBe(mockToken)
    })

    it('应该处理登录错误', async () => {
      vi.mocked(apiClient.post).mockRejectedValueOnce(
        new Error('邮箱或密码错误')
      )

      await expect(
        authService.login('test@example.com', 'wrongpassword')
      ).rejects.toThrow('邮箱或密码错误')
    })
  })

  describe('getCurrentUser', () => {
    it('应该获取当前用户信息', async () => {
      vi.mocked(apiClient.get).mockResolvedValueOnce(mockUser)

      const result = await authService.getCurrentUser()

      expect(apiClient.get).toHaveBeenCalledWith('/api/v1/auth/me')
      expect(result).toEqual(mockUser)
    })

    it('应该处理未登录状态', async () => {
      const error = new Error('Unauthorized')
      error.name = 'ApiError'
      vi.mocked(apiClient.get).mockRejectedValueOnce(error)

      await expect(authService.getCurrentUser()).rejects.toThrow()
    })
  })

  describe('logout', () => {
    it('应该清除 token', () => {
      setAccessToken(mockToken)
      expect(getAccessToken()).toBe(mockToken)

      authService.logout()
      expect(getAccessToken()).toBeNull()
    })
  })

  describe('isAuthenticated', () => {
    it('有 token 时返回 true', () => {
      setAccessToken(mockToken)
      expect(authService.isAuthenticated()).toBe(true)
    })

    it('没有 token 时返回 false', () => {
      clearAccessToken()
      expect(authService.isAuthenticated()).toBe(false)
    })
  })
})
