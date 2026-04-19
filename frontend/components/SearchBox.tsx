'use client'

import { useState, FormEvent } from 'react'
import { Search } from 'lucide-react'

interface SearchBoxProps {
  onSearch: (query: string) => void
  placeholder?: string
}

export default function SearchBox({ onSearch, placeholder = '搜索内容...' }: SearchBoxProps) {
  const [query, setQuery] = useState('')

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault()
    const trimmedQuery = query.trim()
    if (trimmedQuery) {
      onSearch(trimmedQuery)
    }
  }

  return (
    <form onSubmit={handleSubmit} className="flex gap-2 w-full max-w-2xl">
      <input
        type="text"
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        placeholder={placeholder}
        className="flex-1 px-4 py-3 bg-white border-2 border-black rounded-none font-mono text-sm focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-black placeholder:text-stone-400"
      />
      <button
        type="submit"
        className="px-6 py-3 bg-black text-white font-bold rounded-none hover:bg-stone-800 transition-colors"
      >
        <Search className="w-5 h-5" />
      </button>
    </form>
  )
}
