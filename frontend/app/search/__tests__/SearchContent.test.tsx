import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import SearchContent from '../SearchContent'

// Mock next/navigation
const mockPush = vi.fn()
const mockSearchParams = {
  get: vi.fn(() => '测试查询'),
  toString: vi.fn(() => 'q=测试查询'),
}

vi.mock('next/navigation', () => ({
  useSearchParams: vi.fn(() => mockSearchParams),
  useRouter: vi.fn(() => ({
    push: mockPush,
  })),
}))

// Mock search service
vi.mock('@/lib/api/search', () => ({
  searchService: {
    searchText: vi.fn().mockResolvedValue({
      results: [
        {
          id: '1',
          type: 'text' as const,
          title: '测试结果 1',
          description: '测试描述',
          file_path: null,
          source: 'private' as const,
          owner_id: 'user1',
          tags: null,
          status: 'indexed',
          extra_metadata: { relevance: 0.95 },
          created_at: '2024-01-01T00:00:00Z',
          updated_at: '2024-01-01T00:00:00Z',
        },
        {
          id: '2',
          type: 'text' as const,
          title: '测试结果 2',
          description: '测试描述',
          file_path: null,
          source: 'private' as const,
          owner_id: 'user1',
          tags: null,
          status: 'indexed',
          extra_metadata: { relevance: 0.87 },
          created_at: '2024-01-01T00:00:00Z',
          updated_at: '2024-01-01T00:00:00Z',
        },
      ],
      total: 2,
      limit: 20,
    }),
  },
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
  default: ({ onSearch, defaultValue }: { onSearch: (q: string) => void; defaultValue?: string }) => (
    <input
      data-testid="search-box"
      defaultValue={defaultValue}
      onChange={(e) => onSearch(e.target.value)}
    />
  )
}))

describe('SearchContent', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('应该渲染搜索框', () => {
    render(<SearchContent />)
    expect(screen.getByTestId('search-box')).toBeInTheDocument()
  })

  it('应该渲染对话区域', async () => {
    render(<SearchContent />)
    await waitFor(() => {
      expect(screen.getAllByTestId('chat-bubble').length).toBe(2)
    })
  })

  it('应该渲染搜索结果区域', async () => {
    render(<SearchContent />)
    await waitFor(() => {
      expect(screen.getByText('搜索结果 (2)')).toBeInTheDocument()
    })
  })

  it('应该渲染内容卡片', async () => {
    render(<SearchContent />)
    await waitFor(() => {
      expect(screen.getAllByTestId('content-card').length).toBeGreaterThan(0)
    })
  })

  it('应该显示用户消息', async () => {
    render(<SearchContent />)
    await waitFor(() => {
      const userBubbles = screen.getAllByTestId('chat-bubble').filter(
        (el) => el.getAttribute('data-role') === 'user'
      )
      expect(userBubbles.length).toBe(1)
    })
  })

  it('应该显示 AI 回复', async () => {
    render(<SearchContent />)
    await waitFor(() => {
      const assistantBubbles = screen.getAllByTestId('chat-bubble').filter(
        (el) => el.getAttribute('data-role') === 'assistant'
      )
      expect(assistantBubbles.length).toBe(1)
    })
  })

  it('应该显示结果数量', async () => {
    render(<SearchContent />)
    await waitFor(() => {
      expect(screen.getByText(/找到了.*个相关结果/)).toBeInTheDocument()
    })
  })

  it('应该有左右分栏布局', () => {
    const { container } = render(<SearchContent />)
    const mainContainer = container.firstChild as HTMLElement
    expect(mainContainer).toHaveClass('flex')
  })
})
