'use client'

interface ChatBubbleProps {
  role: 'user' | 'assistant'
  content: string
}

export default function ChatBubble({ role, content }: ChatBubbleProps) {
  const isUser = role === 'user'

  return (
    <div
      data-testid="chat-bubble"
      className={`
        flex ${isUser ? 'justify-end' : 'justify-start'} mb-4
      `}
    >
      <div
        className={`
          max-w-[70%] px-4 py-3 font-mono text-sm
          ${isUser ? 'bg-stone-200' : 'bg-stone-100'}
          border-2 border-tech
        `}
      >
        <div className="whitespace-pre-wrap">{content}</div>
      </div>
    </div>
  )
}
