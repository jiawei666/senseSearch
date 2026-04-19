/**
 * 内容上传 API 服务
 */
import { apiClient, ApiError } from './client'

/**
 * 内容类型
 */
export type ContentType = 'image' | 'video'

/**
 * 内容来源
 */
export type ContentSource = 'private' | 'public'

/**
 * 内容接口
 */
export interface Content {
  id: string
  type: ContentType
  title: string
  description: string | null
  file_path: string | null
  source: ContentSource
  owner_id: string | null
  tags: string[] | null
  status: string
  extra_metadata: Record<string, unknown> | null
  created_at: string
  updated_at: string
}

/**
 * 上传请求接口
 */
export interface UploadRequest {
  file: File
  title: string
  description?: string
  source?: ContentSource
  tags?: string
}

/**
 * 上传响应接口
 */
export interface UploadResponse extends Content {}

/**
 * 索引状态响应
 */
export interface IndexStatus {
  content_id: string
  status: string
  indexed_at: string | null
  error_message: string | null
}

/**
 * 内容列表请求接口
 */
export interface ListContentParams {
  owner?: string
  content_type?: ContentType
  source?: ContentSource
  status?: string
  limit?: number
  offset?: number
}

/**
 * 内容列表响应接口
 */
export interface ListContentResponse {
  items: Content[]
  total: number
  limit: number
  offset: number
}

/**
 * 更新内容请求接口
 */
export interface UpdateContentRequest {
  title?: string
  description?: string
  tags?: string
}

/**
 * 上传服务
 */
export const uploadService = {
  /**
   * 上传文件（图片或视频）
   */
  async upload(params: UploadRequest): Promise<UploadResponse> {
    try {
      const formData = new FormData()
      formData.append('file', params.file)
      formData.append('title', params.title)
      if (params.description) formData.append('description', params.description)
      if (params.source) formData.append('source', params.source)
      if (params.tags) formData.append('tags', params.tags)

      const response = await apiClient.upload<UploadResponse>(
        '/api/v1/content/upload',
        formData
      )
      return response
    } catch (error) {
      if (error instanceof ApiError) {
        throw new Error(error.data?.detail || '上传失败')
      }
      throw error
    }
  },

  /**
   * 获取内容详情
   */
  async getContent(id: string): Promise<Content> {
    try {
      const response = await apiClient.get<Content>(
        `/api/v1/content/${id}`
      )
      return response
    } catch (error) {
      if (error instanceof ApiError) {
        throw new Error(error.data?.detail || '获取内容失败')
      }
      throw error
    }
  },

  /**
   * 列出内容
   */
  async listContents(params?: ListContentParams): Promise<ListContentResponse> {
    try {
      const queryParams = new URLSearchParams()
      if (params?.owner) queryParams.append('owner', params.owner)
      if (params?.content_type) queryParams.append('content_type', params.content_type)
      if (params?.source) queryParams.append('source', params.source)
      if (params?.status) queryParams.append('status', params.status)
      if (params?.limit) queryParams.append('limit', String(params.limit))
      if (params?.offset) queryParams.append('offset', String(params.offset))

      const response = await apiClient.get<ListContentResponse>(
        `/api/v1/content?${queryParams.toString()}`
      )
      return response
    } catch (error) {
      if (error instanceof ApiError) {
        throw new Error(error.data?.detail || '获取内容列表失败')
      }
      throw error
    }
  },

  /**
   * 更新内容
   */
  async updateContent(id: string, params: UpdateContentRequest): Promise<Content> {
    try {
      const formData = new FormData()
      if (params.title) formData.append('title', params.title)
      if (params.description) formData.append('description', params.description)
      if (params.tags) formData.append('tags', params.tags)

      const response = await apiClient.upload<Content>(
        `/api/v1/content/${id}`,
        formData
      )
      return response
    } catch (error) {
      if (error instanceof ApiError) {
        throw new Error(error.data?.detail || '更新内容失败')
      }
      throw error
    }
  },

  /**
   * 删除内容
   */
  async deleteContent(id: string): Promise<void> {
    try {
      await apiClient.delete<void>(`/api/v1/content/${id}`)
    } catch (error) {
      if (error instanceof ApiError) {
        throw new Error(error.data?.detail || '删除内容失败')
      }
      throw error
    }
  },

  /**
   * 触发内容索引
   */
  async triggerIndex(id: string): Promise<IndexStatus> {
    try {
      const response = await apiClient.post<IndexStatus>(
        `/api/v1/content/${id}/index`
      )
      return response
    } catch (error) {
      if (error instanceof ApiError) {
        throw new Error(error.data?.detail || '触发索引失败')
      }
      throw error
    }
  },
}
