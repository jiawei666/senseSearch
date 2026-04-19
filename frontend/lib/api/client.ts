/**
 * API 客户端 - 处理所有 HTTP 请求
 */
const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000'

const STORAGE_KEY = 'accessToken'

// 内存中的 token（用于 SSR 和测试环境）
let memoryToken: string | null = null

/**
 * 重置内存中的 token（仅用于测试）
 */
export function __resetMemoryTokenForTesting(): void {
  memoryToken = null
}

/**
 * 获取存储的 access token
 */
export function getAccessToken(): string | null {
  // 优先返回内存中的 token
  if (memoryToken) return memoryToken

  // 尝试从 localStorage 获取
  if (typeof localStorage !== 'undefined') {
    const token = localStorage.getItem(STORAGE_KEY)
    if (token) {
      memoryToken = token
      return token
    }
  }
  return null
}

/**
 * 设置 access token
 */
export function setAccessToken(token: string): void {
  memoryToken = token
  if (typeof localStorage !== 'undefined') {
    localStorage.setItem(STORAGE_KEY, token)
  }
}

/**
 * 清除 access token
 */
export function clearAccessToken(): void {
  memoryToken = null
  if (typeof localStorage !== 'undefined') {
    localStorage.removeItem(STORAGE_KEY)
  }
}

/**
 * API 响应错误
 */
export class ApiError extends Error {
  constructor(
    message: string,
    public status?: number,
    public data?: unknown
  ) {
    super(message)
    this.name = 'ApiError'
  }
}

/**
 * API 响应接口
 */
export interface ApiResponse<T = unknown> {
  data?: T
  detail?: string
}

/**
 * 构建请求头
 */
function buildHeaders(): HeadersInit {
  const headers: HeadersInit = {
    'Content-Type': 'application/json',
  }

  const token = getAccessToken()
  if (token) {
    headers['Authorization'] = `Bearer ${token}`
  }

  return headers
}

/**
 * 处理响应
 */
async function handleResponse<T>(response: Response): Promise<T> {
  const contentType = response.headers.get('content-type')
  const isJson = contentType?.includes('application/json')

  let data: unknown
  if (isJson) {
    data = await response.json()
  } else {
    data = await response.text()
  }

  if (!response.ok) {
    // 401 未授权，清除 token
    if (response.status === 401) {
      clearAccessToken()
      // 触发自定义事件，通知需要重新登录
      if (typeof window !== 'undefined') {
        window.dispatchEvent(new CustomEvent('auth:unauthorized'))
      }
    }

    const message =
      isJson && typeof data === 'object' && data !== null && 'detail' in data
        ? String((data as { detail: string }).detail)
        : response.statusText || '请求失败'

    throw new ApiError(message, response.status, data)
  }

  return data as T
}

/**
 * API 客户端
 */
export const apiClient = {
  /**
   * GET 请求
   */
  async get<T>(endpoint: string): Promise<T> {
    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
      method: 'GET',
      headers: buildHeaders(),
    })
    return handleResponse<T>(response)
  },

  /**
   * POST 请求
   */
  async post<T>(endpoint: string, data?: unknown): Promise<T> {
    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
      method: 'POST',
      headers: buildHeaders(),
      body: data ? JSON.stringify(data) : undefined,
    })
    return handleResponse<T>(response)
  },

  /**
   * PUT 请求
   */
  async put<T>(endpoint: string, data?: unknown): Promise<T> {
    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
      method: 'PUT',
      headers: buildHeaders(),
      body: data ? JSON.stringify(data) : undefined,
    })
    return handleResponse<T>(response)
  },

  /**
   * DELETE 请求
   */
  async delete<T>(endpoint: string): Promise<T> {
    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
      method: 'DELETE',
      headers: buildHeaders(),
    })
    return handleResponse<T>(response)
  },

  /**
   * 上传文件（使用 FormData）
   */
  async upload<T>(endpoint: string, formData: FormData, onProgress?: (progress: number) => void): Promise<T> {
    return new Promise((resolve, reject) => {
      const xhr = new XMLHttpRequest()

      // 设置 token
      const token = getAccessToken()
      if (token) {
        xhr.setRequestHeader('Authorization', `Bearer ${token}`)
      }

      // 监听上传进度
      if (onProgress) {
        xhr.upload.addEventListener('progress', (event) => {
          if (event.lengthComputable) {
            const progress = Math.round((event.loaded / event.total) * 100)
            onProgress(progress)
          }
        })
      }

      // 监听完成
      xhr.addEventListener('load', () => {
        if (xhr.status >= 200 && xhr.status < 300) {
          try {
            const data = JSON.parse(xhr.responseText)
            resolve(data as T)
          } catch {
            resolve(xhr.responseText as unknown as T)
          }
        } else {
          // 401 清除 token
          if (xhr.status === 401) {
            clearAccessToken()
            if (typeof window !== 'undefined') {
              window.dispatchEvent(new CustomEvent('auth:unauthorized'))
            }
          }

          try {
            const data = JSON.parse(xhr.responseText)
            reject(new ApiError(
              typeof data === 'object' && 'detail' in data ? String(data.detail) : '上传失败',
              xhr.status,
              data
            ))
          } catch {
            reject(new ApiError('上传失败', xhr.status))
          }
        }
      })

      // 监听错误
      xhr.addEventListener('error', () => {
        reject(new ApiError('网络错误'))
      })

      // 监听取消
      xhr.addEventListener('abort', () => {
        reject(new ApiError('上传已取消'))
      })

      xhr.open('POST', `${API_BASE_URL}${endpoint}`)
      xhr.send(formData)
    })
  },
}
