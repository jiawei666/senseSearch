import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import Layout from '../Layout'

describe('Layout', () => {
  it('应该渲染子元素', () => {
    render(
      <Layout>
        <div>测试内容</div>
      </Layout>
    )

    expect(screen.getByText('测试内容')).toBeInTheDocument()
  })

  it('应该渲染导航栏', () => {
    render(
      <Layout>
        <div>测试内容</div>
      </Layout>
    )

    expect(screen.getByRole('navigation')).toBeInTheDocument()
  })

  it('导航栏应该包含 Logo 和链接', () => {
    render(
      <Layout>
        <div>测试内容</div>
      </Layout>
    )

    expect(screen.getByText('SenseSearch')).toBeInTheDocument()
  })
})
