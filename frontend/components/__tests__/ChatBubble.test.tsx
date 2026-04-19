import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import ChatBubble from '../ChatBubble'

describe('ChatBubble', () => {
  it('应该渲染用户消息气泡', () => {
    render(<ChatBubble role="user" content="用户消息" />)
    expect(screen.getByText('用户消息')).toBeInTheDocument()
  })

  it('应该渲染 AI 消息气泡', () => {
    render(<ChatBubble role="assistant" content="AI 回复" />)
    expect(screen.getByText('AI 回复')).toBeInTheDocument()
  })

  it('应该根据角色应用不同样式', () => {
    const { container: userContainer } = render(
      <ChatBubble role="user" content="用户消息" />
    )
    const { container: aiContainer } = render(
      <ChatBubble role="assistant" content="AI 回复" />
    )

    const userBubble = userContainer.querySelector('[data-testid="chat-bubble"]')
    const aiBubble = aiContainer.querySelector('[data-testid="chat-bubble"]')

    // 检查外层容器的布局样式
    expect(userBubble).toHaveClass('justify-end')
    expect(aiBubble).toHaveClass('justify-start')
  })

  it('应该显示完整的消息内容', () => {
    render(
      <ChatBubble
        role="assistant"
        content="这是一条完整消息"
      />
    )

    expect(screen.getByText('这是一条完整消息')).toBeInTheDocument()
  })
})
