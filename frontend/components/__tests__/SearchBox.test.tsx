import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import SearchBox from '../SearchBox'

describe('SearchBox', () => {
  describe('基础搜索功能', () => {
    it('应该渲染搜索输入框', () => {
      render(<SearchBox onSearch={vi.fn()} />)
      expect(screen.getByPlaceholderText('搜索内容...')).toBeInTheDocument()
    })

    it('应该在按下回车时触发 onSearch 回调', async () => {
      const user = userEvent.setup()
      const onSearch = vi.fn()
      render(<SearchBox onSearch={onSearch} />)

      const input = screen.getByPlaceholderText('搜索内容...')
      await user.type(input, 'test query{Enter}')

      expect(onSearch).toHaveBeenCalledWith('test query', [])
    })

    it('应该支持点击搜索按钮', async () => {
      const user = userEvent.setup()
      const onSearch = vi.fn()
      render(<SearchBox onSearch={onSearch} />)

      const input = screen.getByPlaceholderText('搜索内容...')
      await user.type(input, 'test query')

      const submitButton = screen.getAllByRole('button')[0] // 第一个按钮是搜索按钮
      await user.click(submitButton)

      expect(onSearch).toHaveBeenCalledWith('test query', [])
    })

    it('应该清空空搜索请求', async () => {
      const user = userEvent.setup()
      const onSearch = vi.fn()
      render(<SearchBox onSearch={onSearch} />)

      const input = screen.getByPlaceholderText('搜索内容...')
      await user.type(input, '   {Enter}')

      expect(onSearch).not.toHaveBeenCalled()
    })

    it('应该只传递查询字符串当没有文件时', async () => {
      const user = userEvent.setup()
      const onSearch = vi.fn()
      render(<SearchBox onSearch={onSearch} />)

      const input = screen.getByPlaceholderText('搜索内容...')
      await user.type(input, 'hello world{Enter}')

      expect(onSearch).toHaveBeenCalledTimes(1)
      expect(onSearch).toHaveBeenCalledWith('hello world', [])
    })
  })

  describe('文件上传功能', () => {
    it('应该渲染图片上传按钮', () => {
      render(<SearchBox onSearch={vi.fn()} />)
      expect(screen.getByLabelText('上传图片')).toBeInTheDocument()
    })

    it('应该渲染视频上传按钮', () => {
      render(<SearchBox onSearch={vi.fn()} />)
      expect(screen.getByLabelText('上传视频')).toBeInTheDocument()
    })

    it('应该显示拖拽上传区域', () => {
      render(<SearchBox onSearch={vi.fn()} />)
      expect(screen.getByText(/拖拽文件到此处上传/)).toBeInTheDocument()
    })

    it('应该显示支持文件类型提示', () => {
      render(<SearchBox onSearch={vi.fn()} />)
      expect(screen.getByText(/支持 PNG, JPG, GIF, WEBP/)).toBeInTheDocument()
    })
  })

  describe('文件预览功能', () => {
    it('选择图片后应该显示预览', async () => {
      const user = userEvent.setup()
      const onSearch = vi.fn()
      render(<SearchBox onSearch={onSearch} />)

      const imageInput = screen.getByLabelText('上传图片')
      const file = new File(['test'], 'test.jpg', { type: 'image/jpeg' })

      await user.upload(imageInput, file)

      expect(screen.getByText('test.jpg')).toBeInTheDocument()
    })

    it('选择视频后应该显示预览', async () => {
      const user = userEvent.setup()
      const onSearch = vi.fn()
      render(<SearchBox onSearch={onSearch} />)

      const videoInput = screen.getByLabelText('上传视频')
      const file = new File(['test'], 'test.mp4', { type: 'video/mp4' })

      await user.upload(videoInput, file)

      expect(screen.getByText('test.mp4')).toBeInTheDocument()
    })

    it('应该能够删除已选文件', async () => {
      const user = userEvent.setup()
      const onSearch = vi.fn()
      render(<SearchBox onSearch={onSearch} />)

      const imageInput = screen.getByLabelText('上传图片')
      const file = new File(['test'], 'test.jpg', { type: 'image/jpeg' })

      await user.upload(imageInput, file)

      const removeButton = screen.getByLabelText('删除文件')
      await user.click(removeButton)

      expect(screen.queryByText('test.jpg')).not.toBeInTheDocument()
    })

    it('搜索时应该传递选中的文件', async () => {
      const user = userEvent.setup()
      const onSearch = vi.fn()
      render(<SearchBox onSearch={onSearch} />)

      const imageInput = screen.getByLabelText('上传图片')
      const file = new File(['test'], 'test.jpg', { type: 'image/jpeg' })

      await user.upload(imageInput, file)

      const input = screen.getByPlaceholderText('搜索内容...')
      await user.type(input, 'test{Enter}')

      expect(onSearch).toHaveBeenCalledWith('test', expect.arrayContaining([
        expect.objectContaining({ name: 'test.jpg', type: 'image' })
      ]))
    })
  })

  describe('拖拽上传', () => {
    it('拖拽文件到区域应该高亮显示', async () => {
      render(<SearchBox onSearch={vi.fn()} />)
      const dropZoneText = screen.getByText(/拖拽文件到此处上传/)
      const dropZone = dropZoneText.closest('div')

      fireEvent.dragEnter(dropZone!)

      expect(dropZone).toHaveClass('border-black')
    })

    it('拖拽离开应该取消高亮', async () => {
      render(<SearchBox onSearch={vi.fn()} />)
      const dropZoneText = screen.getByText(/拖拽文件到此处上传/)
      const dropZone = dropZoneText.closest('div')

      fireEvent.dragEnter(dropZone!)
      fireEvent.dragLeave(dropZone!)

      expect(dropZone).not.toHaveClass('border-black')
    })

    it('应该支持拖拽上传图片文件', () => {
      const onSearch = vi.fn()
      render(<SearchBox onSearch={onSearch} />)

      const dropZoneText = screen.getByText(/拖拽文件到此处上传/)
      const dropZone = dropZoneText.closest('div')

      const file = new File(['test'], 'dropped.jpg', { type: 'image/jpeg' })
      const dataTransfer = {
        files: [file],
        items: [{ kind: 'file', type: 'image/jpeg', getAsFile: () => file }]
      }

      fireEvent.drop(dropZone!, { dataTransfer })

      expect(screen.getByText('dropped.jpg')).toBeInTheDocument()
    })

    it('应该支持拖拽上传视频文件', () => {
      const onSearch = vi.fn()
      render(<SearchBox onSearch={onSearch} />)

      const dropZoneText = screen.getByText(/拖拽文件到此处上传/)
      const dropZone = dropZoneText.closest('div')

      const file = new File(['test'], 'dropped.mp4', { type: 'video/mp4' })
      const dataTransfer = {
        files: [file],
        items: [{ kind: 'file', type: 'video/mp4', getAsFile: () => file }]
      }

      fireEvent.drop(dropZone!, { dataTransfer })

      expect(screen.getByText('dropped.mp4')).toBeInTheDocument()
    })
  })
})
