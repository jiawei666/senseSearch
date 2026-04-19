'use client'

import { useState, FormEvent } from 'react'
import Link from 'next/link'

export interface LoginFormData {
  email: string
  password: string
}

interface LoginFormProps {
  onSubmit: (data: LoginFormData) => void
  isLoading?: boolean
}

export default function LoginForm({ onSubmit, isLoading = false }: LoginFormProps) {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [errors, setErrors] = useState<Partial<Record<keyof LoginFormData, string>>>({})

  const validateEmail = (email: string): boolean => {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
    return emailRegex.test(email)
  }

  const validateForm = (): boolean => {
    const newErrors: Partial<Record<keyof LoginFormData, string>> = {}

    if (!email.trim()) {
      newErrors.email = '请输入邮箱'
    } else if (!validateEmail(email)) {
      newErrors.email = '请输入有效的邮箱地址'
    }

    if (!password) {
      newErrors.password = '请输入密码'
    } else if (password.length < 6) {
      newErrors.password = '密码至少需要6位'
    }

    setErrors(newErrors)
    return Object.keys(newErrors).length === 0
  }

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault()
    if (validateForm()) {
      onSubmit({ email, password })
    }
  }

  const handleEmailBlur = () => {
    if (email && !validateEmail(email)) {
      setErrors((prev) => ({ ...prev, email: '请输入有效的邮箱地址' }))
    } else if (email) {
      setErrors((prev) => ({ ...prev, email: undefined }))
    }
  }

  const handlePasswordBlur = () => {
    if (password && password.length < 6) {
      setErrors((prev) => ({ ...prev, password: '密码至少需要6位' }))
    } else if (password) {
      setErrors((prev) => ({ ...prev, password: undefined }))
    }
  }

  return (
    <div className="w-full max-w-md mx-auto">
      <form onSubmit={handleSubmit} className="space-y-6">
        {/* 邮箱输入 */}
        <div>
          <label htmlFor="email" className="block font-heading text-sm mb-2">
            邮箱
          </label>
          <input
            id="email"
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            onBlur={handleEmailBlur}
            className={`w-full px-4 py-3 bg-white border-2 font-mono text-sm focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-black
              ${errors.email ? 'border-red-500' : 'border-stone-300 focus:border-black'}
            `}
            placeholder="your@email.com"
          />
          {errors.email && (
            <p className="text-red-500 font-code text-xs mt-1">{errors.email}</p>
          )}
        </div>

        {/* 密码输入 */}
        <div>
          <label htmlFor="password" className="block font-heading text-sm mb-2">
            密码
          </label>
          <input
            id="password"
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            onBlur={handlePasswordBlur}
            className={`w-full px-4 py-3 bg-white border-2 font-mono text-sm focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-black
              ${errors.password ? 'border-red-500' : 'border-stone-300 focus:border-black'}
            `}
            placeholder="••••••••"
          />
          {errors.password && (
            <p className="text-red-500 font-code text-xs mt-1">{errors.password}</p>
          )}
        </div>

        {/* 记住我 & 忘记密码 */}
        <div className="flex items-center justify-between">
          <label className="flex items-center gap-2 cursor-pointer">
            <input
              type="checkbox"
              className="w-4 h-4 border-2 border-black bg-white cursor-pointer"
            />
            <span className="font-code text-sm">记住我</span>
          </label>
          <Link
            href="/forgot-password"
            className="font-code text-sm text-stone-600 hover:underline"
          >
            忘记密码？
          </Link>
        </div>

        {/* 提交按钮 */}
        <button
          type="submit"
          disabled={isLoading}
          className="w-full px-6 py-3 bg-black text-white font-heading text-lg font-bold hover:bg-stone-800 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {isLoading ? '登录中...' : '登录'}
        </button>
      </form>

      {/* 注册链接 */}
      <p className="mt-6 text-center font-code text-sm">
        还没有账号？{' '}
        <Link href="/register" className="text-black font-bold hover:underline">
          立即注册
        </Link>
      </p>
    </div>
  )
}
