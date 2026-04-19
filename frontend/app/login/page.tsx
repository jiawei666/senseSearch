'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import Layout from '@/components/Layout'
import { authService } from '@/lib/api/auth'

export default function LoginPage() {
  const router = useRouter()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [isLoading, setIsLoading] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setIsLoading(true)
    setError(null)

    try {
      await authService.login(email, password)
      router.push('/search')
    } catch (err) {
      const message = err instanceof Error ? err.message : '登录失败'
      setError(message)
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <Layout>
      <div className="min-h-[calc(100vh-64px)] flex items-center justify-center">
        <div className="w-full max-w-md p-8 bg-white border-2 border-black">
          <h1 className="font-heading text-3xl mb-8 text-center">登录</h1>

          {error && (
            <div className="mb-6 p-4 bg-red-50 border-2 border-red-500 text-red-700 text-sm">
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-6">
            <div>
              <label htmlFor="email" className="block font-code text-sm mb-2">
                邮箱
              </label>
              <input
                id="email"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                disabled={isLoading}
                className="w-full px-4 py-3 border-2 border-black rounded-none font-mono text-sm focus:outline-none focus:ring-2 focus:ring-black disabled:bg-stone-100"
                required
              />
            </div>

            <div>
              <label htmlFor="password" className="block font-code text-sm mb-2">
                密码
              </label>
              <input
                id="password"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                disabled={isLoading}
                className="w-full px-4 py-3 border-2 border-black rounded-none font-mono text-sm focus:outline-none focus:ring-2 focus:ring-black disabled:bg-stone-100"
                required
              />
            </div>

            <button
              type="submit"
              disabled={isLoading}
              className="w-full px-6 py-3 bg-black text-white font-bold rounded-none hover:bg-stone-800 transition-colors disabled:bg-stone-400 disabled:cursor-not-allowed"
            >
              {isLoading ? '登录中...' : '登录'}
            </button>
          </form>

          <p className="mt-6 text-center text-sm text-muted">
            还没有账号？{' '}
            <a href="/register" className="underline">
              注册
            </a>
          </p>
        </div>
      </div>
    </Layout>
  )
}
