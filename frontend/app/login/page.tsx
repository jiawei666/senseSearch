'use client'

import { useState } from 'react'
import Layout from '@/components/Layout'
import { useRouter } from 'next/navigation'

export default function LoginPage() {
  const router = useRouter()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    // TODO: 对接后端认证 API
    console.log('Login:', { email, password })
    router.push('/')
  }

  return (
    <Layout>
      <div className="min-h-[calc(100vh-64px)] flex items-center justify-center">
        <div className="w-full max-w-md p-8 bg-white border-2 border-black">
          <h1 className="font-heading text-3xl mb-8 text-center">登录</h1>

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
                className="w-full px-4 py-3 border-2 border-black rounded-none font-mono text-sm focus:outline-none focus:ring-2 focus:ring-black"
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
                className="w-full px-4 py-3 border-2 border-black rounded-none font-mono text-sm focus:outline-none focus:ring-2 focus:ring-black"
                required
              />
            </div>

            <button
              type="submit"
              className="w-full px-6 py-3 bg-black text-white font-bold rounded-none hover:bg-stone-800 transition-colors"
            >
              登录
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
