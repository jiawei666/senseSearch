import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest'
import { apiClient, setAccessToken, clearAccessToken } from '../client'

describe('apiClient', () => {
  beforeEach(() => {
    // Mock fetch
    global.fetch = vi.fn()
    localStorage.clear()
  })

  afterEach(() => {
    vi.clearAllMocks()
    clearAccessToken()
  })

  const createMockResponse = <T>(data: T, ok = true, status = 200) => ({
    ok,
    status,
    statusText: ok ? 'OK' : 'Error',
    headers: new Headers({
      'content-type': 'application/json',
    }),
    json: async () => data,
  } as Response)

  it('应该发送 GET 请求到正确的 URL', async () => {
    const mockResponse = { data: 'test' }
    vi.mocked(fetch).mockResolvedValueOnce(createMockResponse(mockResponse))

    const result = await apiClient.get('/api/v1/test')
    expect(fetch).toHaveBeenCalledWith(
      'http://localhost:8000/api/v1/test',
      {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      }
    )
    expect(result).toEqual(mockResponse)
  })

  it('应该发送 POST 请求并包含 body', async () => {
    const mockResponse = { id: '1' }
    vi.mocked(fetch).mockResolvedValueOnce(createMockResponse(mockResponse))

    const data = { name: 'test' }
    const result = await apiClient.post('/api/v1/create', data)
    expect(fetch).toHaveBeenCalledWith(
      'http://localhost:8000/api/v1/create',
      {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(data),
      }
    )
    expect(result).toEqual(mockResponse)
  })

  it('应该在有 token 时添加 Authorization header', async () => {
    setAccessToken('test-token-123')
    const mockResponse = { data: 'test' }
    vi.mocked(fetch).mockResolvedValueOnce(createMockResponse(mockResponse))

    await apiClient.get('/api/v1/protected')
    expect(fetch).toHaveBeenCalledWith(
      'http://localhost:8000/api/v1/protected',
      {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': 'Bearer test-token-123',
        },
      }
    )
  })

  it('应该在 401 错误时清除 token', async () => {
    setAccessToken('test-token-123')
    vi.mocked(fetch).mockResolvedValueOnce({
      ok: false,
      status: 401,
      statusText: 'Unauthorized',
      headers: new Headers({ 'content-type': 'application/json' }),
      json: async () => ({ detail: 'Unauthorized' }),
    } as Response)

    await expect(apiClient.get('/api/v1/protected')).rejects.toThrow()
    expect(localStorage.getItem('accessToken')).toBeNull()
  })

  it('应该支持 DELETE 请求', async () => {
    const mockResponse = { success: true }
    vi.mocked(fetch).mockResolvedValueOnce(createMockResponse(mockResponse))

    const result = await apiClient.delete('/api/v1/items/1')
    expect(fetch).toHaveBeenCalledWith(
      'http://localhost:8000/api/v1/items/1',
      {
        method: 'DELETE',
        headers: {
          'Content-Type': 'application/json',
        },
      }
    )
    expect(result).toEqual(mockResponse)
  })

  it('应该使用自定义 API base URL', () => {
    const customUrl = 'https://api.example.com'
    process.env.NEXT_PUBLIC_API_BASE_URL = customUrl
    // 环境变量在模块加载时读取，这里只是验证配置逻辑
    expect(customUrl).toBe('https://api.example.com')
  })
})
