import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import AuthCallbackPage from '../page'

// Mock next/navigation
const mockPush = vi.fn()
const mockSearchParams = vi.fn()

vi.mock('next/navigation', () => ({
  useSearchParams: () => ({ get: mockSearchParams }),
  useRouter: () => ({ push: mockPush }),
}))

// Mock client token functions
const mockSetAccessToken = vi.fn()
vi.mock('@/lib/api/client', () => ({
  setAccessToken: (token: string) => mockSetAccessToken(token),
}))

describe('AuthCallbackPage', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('有 token 时', () => {
    beforeEach(() => {
      mockSearchParams.mockImplementation((key: string) =>
        key === 'token' ? 'test-token' : null
      )
    })

    it('应该存储 token', () => {
      render(<AuthCallbackPage />)

      expect(mockSetAccessToken).toHaveBeenCalledWith('test-token')
    })
  })

  describe('有 error 时', () => {
    beforeEach(() => {
      mockSearchParams.mockImplementation((key: string) =>
        key === 'error' ? 'Authentication%20failed' : null
      )
    })

    it('应该显示错误信息', () => {
      render(<AuthCallbackPage />)

      expect(screen.getByText('认证失败')).toBeInTheDocument()
      expect(
        screen.getByText('Authentication failed')
      ).toBeInTheDocument()
    })

    it('应该显示重试按钮', () => {
      render(<AuthCallbackPage />)

      const retryLink = screen.getByText('重试')
      expect(retryLink).toBeInTheDocument()
      expect(retryLink.closest('a')).toHaveAttribute('href', '/login')
    })
  })

  describe('无 token 和 error 时', () => {
    beforeEach(() => {
      mockSearchParams.mockReturnValue(null)
    })

    it('应该显示错误信息', () => {
      render(<AuthCallbackPage />)

      expect(screen.getByText('认证失败')).toBeInTheDocument()
      expect(screen.getByText('未收到认证令牌')).toBeInTheDocument()
    })
  })

  describe('加载中状态', () => {
    it('应该显示加载动画', () => {
      mockSearchParams.mockImplementation((key: string) =>
        key === 'token' ? 'test-token' : null
      )

      render(<AuthCallbackPage />)

      expect(screen.getByText('正在认证...')).toBeInTheDocument()
    })
  })
})
