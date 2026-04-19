'use client'

import { useSearchParams } from 'next/navigation'
import ChatBubble from '@/components/ChatBubble'
import ContentCard from '@/components/ContentCard'
import SearchBox from '@/components/SearchBox'

export default function SearchContent() {
  const searchParams = useSearchParams()
  const query = searchParams.get('q') || ''

  // TODO: 对接后端 API
  const mockResults = [
    { id: '1', title: '人工智能基础', content: 'AI 是模拟人类智能的理论和技术...', relevance: 0.95 },
    { id: '2', title: '机器学习入门', content: '机器学习是 AI 的一个分支...', relevance: 0.87 },
    { id: '3', title: '深度学习原理', content: '深度学习使用神经网络...', relevance: 0.82 },
  ]

  const mockConversation = [
    { role: 'user' as const, content: query },
    { role: 'assistant' as const, content: `找到了 ${mockResults.length} 个相关结果。` },
  ]

  const handleSearch = (newQuery: string) => {
    window.location.href = `/search?q=${encodeURIComponent(newQuery)}`
  }

  return (
    <div className="min-h-[calc(100vh-64px)] flex">
      {/* 左侧 AI 对话区 */}
      <div className="w-1/2 p-8 border-r-2 border-black">
        <div className="mb-6">
          <SearchBox onSearch={handleSearch} />
        </div>

        <div className="h-[calc(100vh-200px)] overflow-y-auto">
          {mockConversation.map((msg, i) => (
            <ChatBubble key={i} role={msg.role} content={msg.content} />
          ))}
        </div>
      </div>

      {/* 右侧结果卡片网格 */}
      <div className="w-1/2 p-8">
        <h2 className="font-heading text-2xl mb-6">搜索结果</h2>
        <div className="grid gap-4">
          {mockResults.map((result) => (
            <ContentCard
              key={result.id}
              id={result.id}
              title={result.title}
              content={result.content}
              relevance={result.relevance}
            />
          ))}
        </div>
      </div>
    </div>
  )
}
