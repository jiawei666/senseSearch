/**
 * 搜索 API 服务 - 多模态向量搜索
 */
import { apiClient, ApiError } from './client'

/**
 * 内容类型
 */
export type ContentType = 'text' | 'image' | 'video' | 'document' | 'other'

/**
 * 内容来源
 */
export type ContentSource = 'private' | 'public'

/**
 * 搜索结果接口
 */
export interface SearchResult {
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
 * 搜索响应接口
 */
export interface SearchResponse {
  results: SearchResult[]
  total: number
  limit: number
}

/**
 * 文本搜索请求
 */
export interface TextSearchParams {
  query: string
  limit?: number
}

/**
 * 图片搜索请求
 */
export interface ImageSearchParams {
  file: File
  limit?: number
}

/**
 * 视频搜索请求
 */
export interface VideoSearchParams {
  file: File
  limit?: number
}

/**
 * 混合搜索请求
 */
export interface HybridSearchParams {
  query?: string
  file?: File
  video?: File
  limit?: number
}

/**
 * 搜索服务
 */
export const searchService = {
  /**
   * 文本搜索
   */
  async searchText(params: TextSearchParams): Promise<SearchResponse> {
    try {
      const formData = new FormData()
      formData.append('query', params.query)
      if (params.limit) formData.append('limit', String(params.limit))

      const response = await apiClient.upload<SearchResponse>(
        '/api/v1/search/text',
        formData
      )
      return response
    } catch (error) {
      if (error instanceof ApiError) {
        throw new Error(error.data?.detail || '文本搜索失败')
      }
      throw error
    }
  },

  /**
   * 图片搜索
   */
  async searchImage(params: ImageSearchParams): Promise<SearchResponse> {
    try {
      const formData = new FormData()
      formData.append('file', params.file)
      if (params.limit) formData.append('limit', String(params.limit))

      const response = await apiClient.upload<SearchResponse>(
        '/api/v1/search/image',
        formData
      )
      return response
    } catch (error) {
      if (error instanceof ApiError) {
        throw new Error(error.data?.detail || '图片搜索失败')
      }
      throw error
    }
  },

  /**
   * 视频搜索
   */
  async searchVideo(params: VideoSearchParams): Promise<SearchResponse> {
    try {
      const formData = new FormData()
      formData.append('file', params.file)
      if (params.limit) formData.append('limit', String(params.limit))

      const response = await apiClient.upload<SearchResponse>(
        '/api/v1/search/video',
        formData
      )
      return response
    } catch (error) {
      if (error instanceof ApiError) {
        throw new Error(error.data?.detail || '视频搜索失败')
      }
      throw error
    }
  },

  /**
   * 混合搜索
   */
  async searchHybrid(params: HybridSearchParams): Promise<SearchResponse> {
    try {
      const formData = new FormData()

      if (params.query) formData.append('query', params.query)
      if (params.file) formData.append('file', params.file)
      if (params.video) formData.append('video', params.video)
      if (params.limit) formData.append('limit', String(params.limit))

      const response = await apiClient.upload<SearchResponse>(
        '/api/v1/search/hybrid',
        formData
      )
      return response
    } catch (error) {
      if (error instanceof ApiError) {
        throw new Error(error.data?.detail || '混合搜索失败')
      }
      throw error
    }
  },

  /**
   * 获取搜索历史
   */
  async getHistory(limit: number = 20): Promise<SearchResponse> {
    try {
      const response = await apiClient.get<SearchResponse>(
        `/api/v1/search/history?limit=${limit}`
      )
      return response
    } catch (error) {
      if (error instanceof ApiError) {
        throw new Error(error.data?.detail || '获取搜索历史失败')
      }
      throw error
    }
  },
}

/**
 * 计算相关性分数（从 extra_metadata 中提取）
 */
export function getRelevance(result: SearchResult): number | null {
  return (result.extra_metadata?.relevance as number) || null
}
