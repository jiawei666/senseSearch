import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import RegisterForm from '../RegisterForm'

describe('RegisterForm', () => {
  it('应该渲染邮箱输入框', () => {
    render(<RegisterForm onSubmit={vi.fn()} />)
    expect(screen.getByLabelText(/邮箱/i)).toBeInTheDocument()
  })

  it('应该渲染密码输入框', () => {
    render(<RegisterForm onSubmit={vi.fn()} />)
    const passwordInputs = screen.getAllByLabelText(/密码/i)
    expect(passwordInputs.length).toBe(2)
  })

  it('应该渲染确认密码输入框', () => {
    render(<RegisterForm onSubmit={vi.fn()} />)
    expect(screen.getByLabelText(/确认密码/i)).toBeInTheDocument()
  })

  it('应该渲染注册按钮', () => {
    render(<RegisterForm onSubmit={vi.fn()} />)
    expect(screen.getByRole('button', { name: /注册/i })).toBeInTheDocument()
  })

  it('应该在提交时调用 onSubmit', async () => {
    const user = userEvent.setup()
    const onSubmit = vi.fn()
    render(<RegisterForm onSubmit={onSubmit} />)

    const emailInput = screen.getByLabelText(/邮箱/i)
    const passwordInputs = screen.getAllByLabelText(/密码/i)
    const passwordInput = passwordInputs[0]
    const confirmPasswordInput = screen.getByLabelText(/确认密码/i)
    const submitButton = screen.getByRole('button', { name: /注册/i })

    await user.type(emailInput, 'test@example.com')
    await user.type(passwordInput, 'password123')
    await user.type(confirmPasswordInput, 'password123')
    await user.click(submitButton)

    expect(onSubmit).toHaveBeenCalledWith({
      email: 'test@example.com',
      password: 'password123',
      confirmPassword: 'password123',
    })
  })

  it('应该显示邮箱格式错误提示', async () => {
    const user = userEvent.setup()
    render(<RegisterForm onSubmit={vi.fn()} />)

    const emailInput = screen.getByLabelText(/邮箱/i)
    await user.type(emailInput, 'invalid-email')
    await user.tab() // 触发验证

    expect(screen.getByText(/请输入有效的邮箱地址/i)).toBeInTheDocument()
  })

  it('应该显示密码长度错误提示', async () => {
    const user = userEvent.setup()
    render(<RegisterForm onSubmit={vi.fn()} />)

    const passwordInputs = screen.getAllByLabelText(/密码/i)
    const passwordInput = passwordInputs[0]
    await user.type(passwordInput, '123')
    await user.tab() // 触发验证

    expect(screen.getByText(/密码至少需要6位/i)).toBeInTheDocument()
  })

  it('应该显示密码不匹配错误提示', async () => {
    const user = userEvent.setup()
    render(<RegisterForm onSubmit={vi.fn()} />)

    const passwordInputs = screen.getAllByLabelText(/密码/i)
    const passwordInput = passwordInputs[0]
    const confirmPasswordInput = screen.getByLabelText(/确认密码/i)

    await user.type(passwordInput, 'password123')
    await user.type(confirmPasswordInput, 'different')
    await user.tab() // 触发验证

    expect(screen.getByText(/两次输入的密码不一致/i)).toBeInTheDocument()
  })

  it('密码和确认密码输入框应该是 type="password"', () => {
    render(<RegisterForm onSubmit={vi.fn()} />)
    const passwordInputs = screen.getAllByLabelText(/密码/i) as HTMLInputElement[]
    const confirmPasswordInput = screen.getByLabelText(/确认密码/i) as HTMLInputElement

    expect(passwordInputs[0].type).toBe('password')
    expect(confirmPasswordInput.type).toBe('password')
  })

  it('应该在空表单提交时显示验证错误', async () => {
    const user = userEvent.setup()
    const onSubmit = vi.fn()
    render(<RegisterForm onSubmit={onSubmit} />)

    const submitButton = screen.getByRole('button', { name: /注册/i })
    await user.click(submitButton)

    expect(onSubmit).not.toHaveBeenCalled()
    expect(screen.getByText(/请输入邮箱/i)).toBeInTheDocument()
  })

  it('应该显示服务条款链接', () => {
    render(<RegisterForm onSubmit={vi.fn()} />)
    expect(screen.getByText(/服务条款/i)).toBeInTheDocument()
  })
})
