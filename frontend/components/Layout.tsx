'use client'

import Link from 'next/link'

interface LayoutProps {
  children: React.ReactNode
}

export default function Layout({ children }: LayoutProps) {
  return (
    <div className="min-h-screen flex flex-col">
      <nav role="navigation" className="border-b-2 border-black bg-white px-6 py-4">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <Link href="/" className="font-heading text-2xl tracking-tight">
            SenseSearch
          </Link>
          <div className="flex gap-6 font-code text-sm">
            <Link href="/" className="hover:underline">
              首页
            </Link>
            <Link href="/search" className="hover:underline">
              搜索
            </Link>
            <Link href="/login" className="hover:underline">
              登录
            </Link>
            <Link href="/register" className="hover:underline">
              注册
            </Link>
          </div>
        </div>
      </nav>
      <main className="flex-1">{children}</main>
    </div>
  )
}
