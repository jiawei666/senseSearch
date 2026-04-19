'use client'

import { useState, FormEvent } from 'react'
import Link from 'next/link'

export interface RegisterFormData {
  email: string
  password: string
  confirmPassword: string
}

interface RegisterFormProps {
  onSubmit: (data: RegisterFormData) => void
  isLoading?: boolean
}

export default function RegisterForm({ onSubmit, isLoading = false }: RegisterFormProps) {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [errors, setErrors] = useState<Partial<Record<keyof RegisterFormData, string>>>({})

  const validateEmail = (email: string): boolean => {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
    return emailRegex.test(email)
  }

  const validateForm = (): boolean => {
    const newErrors: Partial<Record<keyof RegisterFormData, string>> = {}

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

    if (!confirmPassword) {
      newErrors.confirmPassword = '请确认密码'
    } else if (password !== confirmPassword) {
      newErrors.confirmPassword = '两次输入的密码不一致'
    }

    setErrors(newErrors)
    return Object.keys(newErrors).length === 0
  }

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault()
    if (validateForm()) {
      onSubmit({ email, password, confirmPassword })
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

  const handleConfirmPasswordBlur = () => {
    if (confirmPassword && password !== confirmPassword) {
      setErrors((prev) => ({ ...prev, confirmPassword: '两次输入的密码不一致' }))
    } else if (confirmPassword) {
      setErrors((prev) => ({ ...prev, confirmPassword: undefined }))
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
            placeholder="至少6位字符"
          />
          {errors.password && (
            <p className="text-red-500 font-code text-xs mt-1">{errors.password}</p>
          )}
        </div>

        {/* 确认密码输入 */}
        <div>
          <label htmlFor="confirmPassword" className="block font-heading text-sm mb-2">
            确认密码
          </label>
          <input
            id="confirmPassword"
            type="password"
            value={confirmPassword}
            onChange={(e) => setConfirmPassword(e.target.value)}
            onBlur={handleConfirmPasswordBlur}
            className={`w-full px-4 py-3 bg-white border-2 font-mono text-sm focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-black
              ${errors.confirmPassword ? 'border-red-500' : 'border-stone-300 focus:border-black'}
            `}
            placeholder="再次输入密码"
          />
          {errors.confirmPassword && (
            <p className="text-red-500 font-code text-xs mt-1">{errors.confirmPassword}</p>
          )}
        </div>

        {/* 服务条款 */}
        <div className="flex items-start gap-2">
          <input
            type="checkbox"
            className="w-4 h-4 mt-1 border-2 border-black bg-white cursor-pointer"
          />
          <p className="font-code text-sm text-stone-600">
            我已阅读并同意{' '}
            <Link href="/terms" className="text-black font-bold hover:underline">
              服务条款
            </Link>
            {' '}和{' '}
            <Link href="/privacy" className="text-black font-bold hover:underline">
              隐私政策
            </Link>
          </p>
        </div>

        {/* 提交按钮 */}
        <button
          type="submit"
          disabled={isLoading}
          className="w-full px-6 py-3 bg-black text-white font-heading text-lg font-bold hover:bg-stone-800 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {isLoading ? '注册中...' : '注册'}
        </button>
      </form>

      {/* 登录链接 */}
      <p className="mt-6 text-center font-code text-sm">
        已有账号？{' '}
        <Link href="/login" className="text-black font-bold hover:underline">
          立即登录
        </Link>
      </p>
    </div>
  )
}
