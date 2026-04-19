import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import SearchBox from '../SearchBox'

describe('SearchBox', () => {
  it('应该渲染搜索输入框', () => {
    render(<SearchBox onSearch={vi.fn()} />)
    expect(screen.getByPlaceholderText('搜索内容...')).toBeInTheDocument()
  })

  it('应该在按下回车时触发 onSearch 回调', async () => {
    const user = userEvent.setup()
    const onSearch = vi.fn()
    render(<SearchBox onSearch={onSearch} />)

    const input = screen.getByPlaceholderText('搜索内容...')
    await user.type(input, 'test query{Enter}')

    expect(onSearch).toHaveBeenCalledWith('test query')
  })

  it('应该支持点击搜索按钮', async () => {
    const user = userEvent.setup()
    const onSearch = vi.fn()
    render(<SearchBox onSearch={onSearch} />)

    const input = screen.getByPlaceholderText('搜索内容...')
    await user.type(input, 'test query')

    const button = screen.getByRole('button')
    await user.click(button)

    expect(onSearch).toHaveBeenCalledWith('test query')
  })

  it('应该清空空搜索请求', async () => {
    const user = userEvent.setup()
    const onSearch = vi.fn()
    render(<SearchBox onSearch={onSearch} />)

    const input = screen.getByPlaceholderText('搜索内容...')
    await user.type(input, '   {Enter}')

    expect(onSearch).not.toHaveBeenCalled()
  })
})
