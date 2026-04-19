import { test, expect } from '@playwright/test'

/**
 * 认证流程 E2E 测试
 */
test.describe('用户认证流程', () => {
  test('应该能够注册新用户', async ({ page }) => {
    await page.goto('/register')

    // 填写注册表单
    await page.fill('input[name="username"]', 'testuser')
    await page.fill('input[name="email"]', `test-${Date.now()}@example.com`)
    await page.fill('input[name="password"]', 'Password123')
    await page.fill('input[name="confirmPassword"]', 'Password123')

    // 提交表单
    await page.click('button[type="submit"]')

    // 等待跳转到登录页
    await expect(page).toHaveURL(/\/login/)
  })

  test('应该拒绝密码不匹配的注册', async ({ page }) => {
    await page.goto('/register')

    await page.fill('input[name="username"]', 'testuser')
    await page.fill('input[name="email"]', 'test@example.com')
    await page.fill('input[name="password"]', 'Password123')
    await page.fill('input[name="confirmPassword"]', 'DifferentPassword')

    await page.click('button[type="submit"]')

    // 应该显示错误消息
    await expect(page.getByText('密码不匹配')).toBeVisible()
  })

  test('应该能够登录', async ({ page }) => {
    // 首先注册测试用户（如果不存在）
    await page.goto('/register')
    await page.fill('input[name="username"]', 'e2etestuser')
    await page.fill('input[name="email"]', 'e2etest@example.com')
    await page.fill('input[name="password"]', 'Password123')
    await page.fill('input[name="confirmPassword"]', 'Password123')
    await page.click('button[type="submit"]')
    await page.waitForURL(/\/login/)

    // 登录
    await page.goto('/login')
    await page.fill('input[name="email"]', 'e2etest@example.com')
    await page.fill('input[name="password"]', 'Password123')
    await page.click('button[type="submit"]')

    // 应该跳转到搜索页
    await expect(page).toHaveURL(/\/search/)
  })

  test('应该拒绝错误的登录凭据', async ({ page }) => {
    await page.goto('/login')

    await page.fill('input[name="email"]', 'wrong@example.com')
    await page.fill('input[name="password"]', 'wrongpassword')
    await page.click('button[type="submit"]')

    // 应该显示错误消息
    await expect(page.getByText(/登录失败|密码错误/)).toBeVisible()
  })
})

/**
 * 搜索功能 E2E 测试
 */
test.describe('搜索功能', () => {
  test.beforeEach(async ({ page }) => {
    // 登录
    await page.goto('/login')
    await page.fill('input[name="email"]', 'e2etest@example.com')
    await page.fill('input[name="password"]', 'Password123')
    await page.click('button[type="submit"]')
    await page.waitForURL(/\/search/)
  })

  test('应该显示搜索页面', async ({ page }) => {
    await expect(page.getByPlaceholder('搜索内容...')).toBeVisible()
    await expect(page.getByText('搜索结果')).toBeVisible()
  })

  test('应该能够执行文本搜索', async ({ page }) => {
    const searchTerm = '人工智能'
    await page.fill('input[placeholder="搜索内容..."]', searchTerm)
    await page.click('button[type="submit"]')

    // URL 应该包含搜索参数
    await expect(page).toHaveURL(new RegExp(`q=${encodeURIComponent(searchTerm)}`))

    // 应该显示 AI 回复
    await expect(page.getByText(/找到了.*个相关结果/)).toBeVisible()
  })

  test('应该显示上传图片按钮', async ({ page }) => {
    await expect(page.getByText('上传图片')).toBeVisible()
    await expect(page.getByText('上传视频')).toBeVisible()
  })

  test('应该显示拖拽上传区域', async ({ page }) => {
    await expect(page.getByText('拖拽文件到此处上传')).toBeVisible()
  })

  test('应该有左右分栏布局', async ({ page }) => {
    const container = page.locator('.min-h-\\[calc\\(100vh-64px\\)\\]')
    await expect(container).toHaveClass(/flex/)
  })
})

/**
 * 页面导航 E2E 测试
 */
test.describe('页面导航', () => {
  test('应该能够从首页导航到搜索页', async ({ page }) => {
    await page.goto('/')

    // 点击导航链接（根据实际 UI）
    const searchLink = page.getByRole('link', { name: /搜索|search/i })
    if (await searchLink.count() > 0) {
      await searchLink.click()
      await expect(page).toHaveURL(/\/search/)
    }
  })

  test('应该能够导航到登录页', async ({ page }) => {
    await page.goto('/')

    const loginLink = page.getByRole('link', { name: /登录|login/i })
    if (await loginLink.count() > 0) {
      await loginLink.click()
      await expect(page).toHaveURL(/\/login/)
    }
  })

  test('应该能够导航到注册页', async ({ page }) => {
    await page.goto('/login')

    const registerLink = page.getByRole('link', { name: /注册|register/i })
    if (await registerLink.count() > 0) {
      await registerLink.click()
      await expect(page).toHaveURL(/\/register/)
    }
  })

  test('应该能够返回到首页', async ({ page }) => {
    await page.goto('/search')

    const logo = page.getByRole('img', { name: /logo|logo/i })
    if (await logo.count() > 0) {
      await logo.click()
      await expect(page).toHaveURL(/\//)
    }
  })
})

/**
 * 响应式设计 E2E 测试
 */
test.describe('响应式设计', () => {
  const viewports = [
    { name: 'Desktop', width: 1920, height: 1080 },
    { name: 'Laptop', width: 1366, height: 768 },
    { name: 'Tablet', width: 768, height: 1024 },
    { name: 'Mobile', width: 375, height: 667 },
  ]

  for (const viewport of viewports) {
    test(`${viewport.name}: 搜索页应该正确显示`, async ({ page }) => {
      await page.setViewportSize({ width: viewport.width, height: viewport.height })
      await page.goto('/search')

      // 搜索框应该可见
      await expect(page.getByPlaceholder('搜索内容...')).toBeVisible()

      // 搜索结果标题应该可见
      await expect(page.getByText('搜索结果')).toBeVisible()
    })
  }
})

/**
 * 可访问性 E2E 测试
 */
test.describe('可访问性', () => {
  test('登录表单应该有正确的标签', async ({ page }) => {
    await page.goto('/login')

    await expect(page.getByLabel('邮箱')).toBeVisible()
    await expect(page.getByLabel('密码')).toBeVisible()

    // 登录按钮应该有可访问的名称
    const loginButton = page.getByRole('button', { name: '登录' })
    await expect(loginButton).toBeVisible()
  })

  test('注册表单应该有正确的标签', async ({ page }) => {
    await page.goto('/register')

    await expect(page.getByLabel('用户名')).toBeVisible()
    await expect(page.getByLabel('邮箱')).toBeVisible()
    await expect(page.getByLabel('密码')).toBeVisible()
    await expect(page.getByLabel('确认密码')).toBeVisible()
  })

  test('搜索框应该有可访问的标签', async ({ page }) => {
    await page.goto('/search')

    const searchInput = page.getByRole('textbox', { name: /search|搜索/i })
    if (await searchInput.count() > 0) {
      await expect(searchInput).toBeVisible()
    }
  })
})

/**
 * 性能 E2E 测试（使用 Lighthouse 风格的检查）
 */
test.describe('性能检查', () => {
  test('登录页应该快速加载', async ({ page }) => {
    const startTime = Date.now()

    await page.goto('/login')
    await page.waitForLoadState('domcontentloaded')

    const loadTime = Date.now() - startTime
    console.log(`登录页加载时间: ${loadTime}ms`)

    // 页面应该在 3 秒内加载
    expect(loadTime).toBeLessThan(3000)
  })

  test('搜索页应该快速加载', async ({ page }) => {
    const startTime = Date.now()

    await page.goto('/search')
    await page.waitForLoadState('domcontentloaded')

    const loadTime = Date.now() - startTime
    console.log(`搜索页加载时间: ${loadTime}ms`)

    expect(loadTime).toBeLessThan(3000)
  })
})
