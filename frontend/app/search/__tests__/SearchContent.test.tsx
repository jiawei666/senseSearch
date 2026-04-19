import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import SearchContent from '../SearchContent'

// Mock useSearchParams
vi.mock('next/navigation', () => ({
  useSearchParams: vi.fn(() => ({
    get: vi.fn(() => 'test query')
  }))
}))

// Mock child components
vi.mock('@/components/ChatBubble', () => ({
  default: ({ role, content }: { role: string; content: string }) => (
    <div data-testid="chat-bubble" data-role={role}>
      {content}
    </div>
  )
}))

vi.mock('@/components/ContentCard', () => ({
  default: ({ title, content }: { title: string; content: string }) => (
    <div data-testid="content-card">
      <h3>{title}</h3>
      <p>{content}</p>
    </div>
  )
}))

vi.mock('@/components/SearchBox', () => ({
  default: ({ onSearch }: { onSearch: (q: string) => void }) => (
    <input data-testid="search-box" onChange={(e) => onSearch(e.target.value)} />
  )
}))

describe('SearchContent', () => {
  it('应该渲染搜索框', () => {
    render(<SearchContent />)
    expect(screen.getByTestId('search-box')).toBeInTheDocument()
  })

  it('应该渲染对话区域', () => {
    render(<SearchContent />)
    expect(screen.getAllByTestId('chat-bubble').length).toBe(2)
  })

  it('应该渲染搜索结果区域', () => {
    render(<SearchContent />)
    expect(screen.getByText('搜索结果')).toBeInTheDocument()
  })

  it('应该渲染内容卡片', () => {
    render(<SearchContent />)
    expect(screen.getAllByTestId('content-card').length).toBeGreaterThan(0)
  })

  it('应该显示用户消息', () => {
    render(<SearchContent />)
    const userBubbles = screen.getAllByTestId('chat-bubble').filter(
      (el) => el.getAttribute('data-role') === 'user'
    )
    expect(userBubbles.length).toBe(1)
  })

  it('应该显示 AI 回复', () => {
    render(<SearchContent />)
    const assistantBubbles = screen.getAllByTestId('chat-bubble').filter(
      (el) => el.getAttribute('data-role') === 'assistant'
    )
    expect(assistantBubbles.length).toBe(1)
  })

  it('应该显示结果数量', () => {
    render(<SearchContent />)
    expect(screen.getByText(/找到了.*个相关结果/)).toBeInTheDocument()
  })

  it('应该有左右分栏布局', () => {
    const { container } = render(<SearchContent />)
    const mainContainer = container.firstChild as HTMLElement
    expect(mainContainer).toHaveClass('flex')
  })
})
