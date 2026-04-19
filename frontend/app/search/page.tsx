'use client'

import { Suspense } from 'react'
import Layout from '@/components/Layout'
import SearchContent from './SearchContent'

export default function SearchPage() {
  return (
    <Layout>
      <Suspense fallback={<div>加载中...</div>}>
        <SearchContent />
      </Suspense>
    </Layout>
  )
}
