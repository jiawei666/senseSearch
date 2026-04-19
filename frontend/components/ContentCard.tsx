'use client'

import { FileText } from 'lucide-react'

interface ContentCardProps {
  id: string
  title: string
  content: string
  relevance: number
  onClick?: () => void
}

export default function ContentCard({ id, title, content, relevance, onClick }: ContentCardProps) {
  const relevancePercent = Math.round(relevance * 100)

  return (
    <div
      data-testid="content-card"
      onClick={onClick}
      className={`
        bg-card border-2 border-tech p-4 hover:shadow-lg transition-all
        ${onClick ? 'cursor-pointer hover:-translate-y-1' : ''}
      `}
    >
      <div className="flex items-start gap-3">
        <FileText className="w-6 h-6 flex-shrink-0 text-stone-600" />
        <div className="flex-1 min-w-0">
          <h3 className="font-heading text-lg mb-2 line-clamp-1">{title}</h3>
          <p className="text-muted text-sm line-clamp-3 mb-3">{content}</p>
          <div className="flex items-center gap-2 text-xs font-code">
            <span className="px-2 py-1 bg-stone-200">相关性: {relevancePercent}%</span>
          </div>
        </div>
      </div>
    </div>
  )
}
