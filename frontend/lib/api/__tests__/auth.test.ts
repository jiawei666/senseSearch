import { describe, it, expect, beforeEach, vi } from 'vitest'
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

  describe('githubLogin', () => {
    beforeEach(() => {
      // 保存原始的 window.location
      delete (window as any).location
      window.location = { href: '' } as any
    })

    it('应该重定向到 GitHub OAuth 端点', () => {
      const expectedUrl = 'http://localhost:8000/api/v1/auth/github'

      authService.githubLogin()

      expect(window.location.href).toBe(expectedUrl)
    })

    it('应该使用自定义 API_BASE_URL', () => {
      process.env.NEXT_PUBLIC_API_BASE_URL = 'https://api.example.com'
      const expectedUrl = 'https://api.example.com/api/v1/auth/github'

      authService.githubLogin()

      expect(window.location.href).toBe(expectedUrl)

      // 清理
      delete process.env.NEXT_PUBLIC_API_BASE_URL
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
