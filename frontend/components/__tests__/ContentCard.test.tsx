import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import ContentCard from '../ContentCard'

describe('ContentCard', () => {
  it('应该渲染卡片标题和内容', () => {
    render(
      <ContentCard
        id="1"
        title="测试标题"
        content="测试内容"
        relevance={0.95}
      />
    )

    expect(screen.getByText('测试标题')).toBeInTheDocument()
    expect(screen.getByText('测试内容')).toBeInTheDocument()
  })

  it('应该显示相关性分数', () => {
    render(
      <ContentCard
        id="1"
        title="测试标题"
        content="测试内容"
        relevance={0.95}
      />
    )

    expect(screen.getByText(/95%/)).toBeInTheDocument()
  })

  it('应该支持点击事件', () => {
    const handleClick = () => {}
    const { container } = render(
      <ContentCard
        id="1"
        title="测试标题"
        content="测试内容"
        relevance={0.95}
        onClick={handleClick}
      />
    )

    const card = container.querySelector('[data-testid="content-card"]')
    expect(card).toHaveClass('cursor-pointer')
  })
})
