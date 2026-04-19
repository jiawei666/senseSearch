import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import LoginForm from '../LoginForm'

describe('LoginForm', () => {
  it('应该渲染邮箱输入框', () => {
    render(<LoginForm onSubmit={vi.fn()} />)
    expect(screen.getByLabelText(/邮箱/i)).toBeInTheDocument()
  })

  it('应该渲染密码输入框', () => {
    render(<LoginForm onSubmit={vi.fn()} />)
    expect(screen.getByLabelText(/密码/i)).toBeInTheDocument()
  })

  it('应该渲染登录按钮', () => {
    render(<LoginForm onSubmit={vi.fn()} />)
    expect(screen.getByRole('button', { name: /登录/i })).toBeInTheDocument()
  })

  it('应该在提交时调用 onSubmit', async () => {
    const user = userEvent.setup()
    const onSubmit = vi.fn()
    render(<LoginForm onSubmit={onSubmit} />)

    const emailInput = screen.getByLabelText(/邮箱/i)
    const passwordInput = screen.getByLabelText(/密码/i)
    const submitButton = screen.getByRole('button', { name: /登录/i })

    await user.type(emailInput, 'test@example.com')
    await user.type(passwordInput, 'password123')
    await user.click(submitButton)

    expect(onSubmit).toHaveBeenCalledWith({
      email: 'test@example.com',
      password: 'password123',
    })
  })

  it('应该显示邮箱格式错误提示', async () => {
    const user = userEvent.setup()
    render(<LoginForm onSubmit={vi.fn()} />)

    const emailInput = screen.getByLabelText(/邮箱/i)
    await user.type(emailInput, 'invalid-email')
    await user.tab() // 触发验证

    expect(screen.getByText(/请输入有效的邮箱地址/i)).toBeInTheDocument()
  })

  it('应该显示密码长度错误提示', async () => {
    const user = userEvent.setup()
    render(<LoginForm onSubmit={vi.fn()} />)

    const passwordInput = screen.getByLabelText(/密码/i)
    await user.type(passwordInput, '123')
    await user.tab() // 触发验证

    expect(screen.getByText(/密码至少需要6位/i)).toBeInTheDocument()
  })

  it('密码输入框应该是 type="password"', () => {
    render(<LoginForm onSubmit={vi.fn()} />)
    const passwordInput = screen.getByLabelText(/密码/i) as HTMLInputElement
    expect(passwordInput.type).toBe('password')
  })

  it('应该在空表单提交时显示验证错误', async () => {
    const user = userEvent.setup()
    const onSubmit = vi.fn()
    render(<LoginForm onSubmit={onSubmit} />)

    const submitButton = screen.getByRole('button', { name: /登录/i })
    await user.click(submitButton)

    expect(onSubmit).not.toHaveBeenCalled()
    expect(screen.getByText(/请输入邮箱/i)).toBeInTheDocument()
  })

  it('应该显示"记住我"复选框', () => {
    render(<LoginForm onSubmit={vi.fn()} />)
    expect(screen.getByLabelText(/记住我/i)).toBeInTheDocument()
  })

  it('应该显示"忘记密码"链接', () => {
    render(<LoginForm onSubmit={vi.fn()} />)
    expect(screen.getByText(/忘记密码/i)).toBeInTheDocument()
  })
})
