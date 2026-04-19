'use client'

import { useState } from 'react'
import Layout from '@/components/Layout'
import SearchBox from '@/components/SearchBox'
import { Sparkles } from 'lucide-react'

export default function HomePage() {
  const [searchQuery, setSearchQuery] = useState('')

  const handleSearch = (query: string) => {
    setSearchQuery(query)
    window.location.href = `/search?q=${encodeURIComponent(query)}`
  }

  const hotTags = ['人工智能', '机器学习', '深度学习', '数据分析', '云计算']

  return (
    <Layout>
      <div className="min-h-[calc(100vh-64px)] flex">
        {/* 左侧搜索区域 */}
        <div className="w-1/2 flex flex-col justify-center px-16">
          <h1 className="font-heading text-6xl mb-8 tracking-tight">
            智能搜索
            <br />
            <span className="text-stone-600">发现未知</span>
          </h1>

          <div className="mb-8">
            <SearchBox onSearch={handleSearch} />
          </div>

          <div className="flex gap-2 flex-wrap">
            {hotTags.map((tag) => (
              <button
                key={tag}
                onClick={() => handleSearch(tag)}
                className="px-4 py-2 bg-white border-2 border-black font-code text-sm hover:bg-stone-100 transition-colors"
              >
                #{tag}
              </button>
            ))}
          </div>
        </div>

        {/* 右侧视觉区域 */}
        <div className="w-1/2 flex items-center justify-center border-l-2 border-black">
          <div className="text-center p-8">
            <Sparkles className="w-48 h-48 mx-auto mb-6 text-stone-600" />
            <p className="font-code text-muted">
              AI 驱动的语义搜索引擎
            </p>
          </div>
        </div>
      </div>
    </Layout>
  )
}
