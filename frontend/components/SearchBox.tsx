'use client'

import { useState, FormEvent, useRef } from 'react'
import { Search, Image, Video, X, Upload } from 'lucide-react'

interface SelectedFile {
  name: string
  type: 'image' | 'video'
  file: File
}

interface SearchBoxProps {
  onSearch: (query: string, files?: SelectedFile[]) => void
  placeholder?: string
  defaultValue?: string
}

export default function SearchBox({ onSearch, placeholder = '搜索内容...', defaultValue = '' }: SearchBoxProps) {
  const [query, setQuery] = useState(defaultValue)
  const [selectedFiles, setSelectedFiles] = useState<SelectedFile[]>([])
  const [isDragging, setIsDragging] = useState(false)
  const imageInputRef = useRef<HTMLInputElement>(null)
  const videoInputRef = useRef<HTMLInputElement>(null)

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault()
    const trimmedQuery = query.trim()
    if (trimmedQuery || selectedFiles.length > 0) {
      onSearch(trimmedQuery, selectedFiles)
    }
  }

  const handleImageUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files
    if (files && files[0]) {
      const file = files[0]
      if (file.type.startsWith('image/')) {
        setSelectedFiles([...selectedFiles, { name: file.name, type: 'image', file }])
      }
    }
  }

  const handleVideoUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files
    if (files && files[0]) {
      const file = files[0]
      if (file.type.startsWith('video/')) {
        setSelectedFiles([...selectedFiles, { name: file.name, type: 'video', file }])
      }
    }
  }

  const handleRemoveFile = (index: number) => {
    setSelectedFiles(selectedFiles.filter((_, i) => i !== index))
  }

  const handleDragEnter = () => setIsDragging(true)
  const handleDragLeave = () => setIsDragging(false)

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(true)
  }

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(false)

    const files = Array.from(e.dataTransfer.files)
    const newFiles: SelectedFile[] = []

    files.forEach((file) => {
      if (file.type.startsWith('image/')) {
        newFiles.push({ name: file.name, type: 'image', file })
      } else if (file.type.startsWith('video/')) {
        newFiles.push({ name: file.name, type: 'video', file })
      }
    })

    if (newFiles.length > 0) {
      setSelectedFiles([...selectedFiles, ...newFiles])
    }
  }

  return (
    <div className="w-full max-w-2xl">
      <form onSubmit={handleSubmit} className="flex gap-2 mb-4">
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

      {/* 文件上传按钮 */}
      <div className="flex gap-2 mb-4">
        <button
          type="button"
          onClick={() => imageInputRef.current?.click()}
          className="flex items-center gap-2 px-4 py-2 bg-white border-2 border-black hover:bg-stone-100 transition-colors font-mono text-sm"
        >
          <Image className="w-4 h-4" />
          上传图片
        </button>
        <input
          ref={imageInputRef}
          type="file"
          accept="image/png,image/jpeg,image/gif,image/webp"
          onChange={handleImageUpload}
          className="hidden"
          aria-label="上传图片"
        />

        <button
          type="button"
          onClick={() => videoInputRef.current?.click()}
          className="flex items-center gap-2 px-4 py-2 bg-white border-2 border-black hover:bg-stone-100 transition-colors font-mono text-sm"
        >
          <Video className="w-4 h-4" />
          上传视频
        </button>
        <input
          ref={videoInputRef}
          type="file"
          accept="video/mp4,video/webm,video/quicktime"
          onChange={handleVideoUpload}
          className="hidden"
          aria-label="上传视频"
        />
      </div>

      {/* 拖拽上传区域 */}
      <div
        onDragEnter={handleDragEnter}
        onDragLeave={handleDragLeave}
        onDragOver={handleDragOver}
        onDrop={handleDrop}
        className={`
          border-2 border-dashed p-6 text-center transition-colors
          ${isDragging ? 'border-black bg-stone-100' : 'border-stone-300'}
        `}
      >
        <Upload className="w-8 h-8 mx-auto mb-2 text-stone-400" />
        <p className="font-mono text-sm text-stone-500 mb-1">拖拽文件到此处上传</p>
        <p className="font-code text-xs text-stone-400">支持 PNG, JPG, GIF, WEBP, MP4, WEBM</p>
      </div>

      {/* 文件预览列表 */}
      {selectedFiles.length > 0 && (
        <div className="mt-4 space-y-2">
          {selectedFiles.map((file, index) => (
            <div
              key={index}
              className="flex items-center justify-between px-4 py-2 bg-white border border-stone-300"
            >
              <div className="flex items-center gap-2">
                {file.type === 'image' ? (
                  <Image className="w-4 h-4 text-stone-500" />
                ) : (
                  <Video className="w-4 h-4 text-stone-500" />
                )}
                <span className="font-mono text-sm">{file.name}</span>
              </div>
              <button
                type="button"
                onClick={() => handleRemoveFile(index)}
                className="p-1 hover:bg-stone-100 transition-colors"
                aria-label="删除文件"
              >
                <X className="w-4 h-4 text-stone-500" />
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
