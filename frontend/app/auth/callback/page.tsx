'use client'

import { useEffect, useState } from 'react'
import { useSearchParams, useRouter } from 'next/navigation'
import { setAccessToken } from '@/lib/api/client'

export default function AuthCallbackPage() {
  const searchParams = useSearchParams()
  const router = useRouter()
  const [error, setError] = useState<string | null>(null)
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    const token = searchParams.get('token')
    const errorParam = searchParams.get('error')

    if (errorParam) {
      setError(decodeURIComponent(errorParam))
      setIsLoading(false)
      return
    }

    if (token) {
      setAccessToken(token)
      router.push('/search')
    } else {
      setError('未收到认证令牌')
      setIsLoading(false)
    }
  }, [searchParams, router])

  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-[#F5F5F5]">
        <div className="w-full max-w-md p-8 bg-white border-2 border-black">
          <h1 className="font-heading text-2xl mb-4 text-center text-black">
            认证失败
          </h1>
          <p className="font-code text-sm mb-6 text-center text-stone-600">
            {error}
          </p>
          <a
            href="/login"
            className="block w-full px-6 py-3 bg-black text-white font-mono font-bold text-center rounded-none hover:bg-stone-800 transition-colors"
          >
            重试
          </a>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-[#F5F5F5]">
      <div className="w-full max-w-md p-8 bg-white border-2 border-black">
        <div className="flex flex-col items-center">
          {/* 加载动画 */}
          <div className="w-8 h-8 border-2 border-black border-t-transparent rounded-full animate-spin mb-4"></div>
          <p className="font-code text-sm text-stone-600">正在认证...</p>
        </div>
      </div>
    </div>
  )
}
