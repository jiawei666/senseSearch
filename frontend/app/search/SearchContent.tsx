'use client'

import { useSearchParams, useRouter } from 'next/navigation'
import { useEffect, useState } from 'react'
import ChatBubble from '@/components/ChatBubble'
import ContentCard from '@/components/ContentCard'
import SearchBox from '@/components/SearchBox'
import { searchService, type SearchResult } from '@/lib/api/search'

interface ConversationMessage {
  role: 'user' | 'assistant'
  content: string
}

export default function SearchContent() {
  const searchParams = useSearchParams()
  const router = useRouter()
  const query = searchParams.get('q') || ''

  const [results, setResults] = useState<SearchResult[]>([])
  const [conversation, setConversation] = useState<ConversationMessage[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // 当查询参数变化时执行搜索
  useEffect(() => {
    if (query) {
      performSearch(query)
    }
  }, [query])

  const performSearch = async (searchQuery: string) => {
    setIsLoading(true)
    setError(null)

    try {
      const response = await searchService.searchText({
        query: searchQuery,
        limit: 20,
      })

      setResults(response.results)

      // 更新对话流
      setConversation([
        { role: 'user', content: searchQuery },
        {
          role: 'assistant',
          content: `找到了 ${response.results.length} 个相关结果。`,
        },
      ])
    } catch (err) {
      const message = err instanceof Error ? err.message : '搜索失败'
      setError(message)
      setConversation([
        { role: 'user', content: searchQuery },
        { role: 'assistant', content: `搜索出错：${message}` },
      ])
    } finally {
      setIsLoading(false)
    }
  }

  const handleSearch = (newQuery: string) => {
    const params = new URLSearchParams(searchParams.toString())
    if (newQuery) {
      params.set('q', newQuery)
    } else {
      params.delete('q')
    }
    router.push(`/search?${params.toString()}`)
  }

  return (
    <div className="min-h-[calc(100vh-64px)] flex">
      {/* 左侧 AI 对话区 */}
      <div className="w-1/2 p-8 border-r-2 border-black">
        <div className="mb-6">
          <SearchBox onSearch={handleSearch} defaultValue={query} />
        </div>

        <div className="h-[calc(100vh-200px)] overflow-y-auto">
          {isLoading && (
            <div className="text-sm text-gray-600">搜索中...</div>
          )}
          {error && (
            <div className="text-sm text-red-600">{error}</div>
          )}
          {conversation.map((msg, i) => (
            <ChatBubble key={i} role={msg.role} content={msg.content} />
          ))}
        </div>
      </div>

      {/* 右侧结果卡片网格 */}
      <div className="w-1/2 p-8">
        <h2 className="font-heading text-2xl mb-6">
          搜索结果 {results.length > 0 && `(${results.length})`}
        </h2>
        {isLoading ? (
          <div className="text-sm text-gray-600">加载中...</div>
        ) : results.length === 0 && query ? (
          <div className="text-sm text-gray-600">没有找到相关结果</div>
        ) : results.length === 0 && !query ? (
          <div className="text-sm text-gray-400">请输入搜索关键词</div>
        ) : (
          <div className="grid gap-4">
            {results.map((result) => (
              <ContentCard
                key={result.id}
                id={result.id}
                title={result.title}
                content={result.description || '暂无描述'}
                relevance={result.extra_metadata?.relevance as number | undefined}
              />
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
