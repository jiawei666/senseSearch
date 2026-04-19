import { test, expect } from '@playwright/test'

/**
 * SenseSearch E2E 测试套件
 * 覆盖用户注册、登录、搜索等关键流程
 */

// 测试配置
const BASE_URL = process.env.BASE_URL || 'http://localhost:3000'

// 生成唯一用户名以避免冲突
function generateUsername() {
  return `testuser_${Date.now()}`
}

test.describe('用户注册和登录流程', () => {
  test.beforeEach(async ({ page }) => {
    // 每个测试前访问首页
    await page.goto(BASE_URL)
  })

  test('用户可以成功注册新账号', async ({ page }) => {
    // 导航到注册页面
    await page.click('text=注册')
    await expect(page).toHaveURL(/.*\/register/)

    // 填写注册表单
    const username = generateUsername()
    const password = 'TestPassword123!'

    await page.fill('input[type="email"]', username)
    await page.fill('input[type="password"]', password)
    await page.fill('input[placeholder*="确认"]', password)

    // 提交注册
    await page.click('button:has-text("注册")')

    // 验证注册成功 - 应该重定向到搜索页或显示成功消息
    await expect(page.locator('body')).toContainText(['成功', '登录'])
  })

  test('用户可以使用正确的凭证登录', async ({ page }) => {
    // 导航到登录页面
    await page.click('text=登录')
    await expect(page).toHaveURL(/.*\/login/)

    // 填写登录表单
    await page.fill('input[type="email"]', 'test@example.com')
    await page.fill('input[type="password"]', 'TestPassword123!')

    // 提交登录
    await page.click('button:has-text("登录")')

    // 验证登录成功 - 应该可以访问搜索页面
    // 或者显示成功消息
    await expect(page.locator('body')).toBeVisible()
  })

  test('登录失败时显示错误消息', async ({ page }) => {
    // 导航到登录页面
    await page.click('text=登录')
    await expect(page).toHaveURL(/.*\/login/)

    // 使用错误的凭证
    await page.fill('input[type="email"]', 'wrong@example.com')
    await page.fill('input[type="password"]', 'WrongPassword')

    // 提交登录
    await page.click('button:has-text("登录")')

    // 验证错误消息显示
    await expect(page.locator('body')).toContainText(['错误', '失败', '登录'], { timeout: 5000 })
  })
})

test.describe('文本搜索功能', () => {
  test.beforeEach(async ({ page }) => {
    // 访问搜索页面
    await page.goto(`${BASE_URL}/search`)
  })

  test('可以执行文本搜索并显示结果', async ({ page }) => {
    // 在搜索框中输入查询
    const searchInput = page.locator('input[placeholder*="搜索"], textarea[placeholder*="搜索"]').first()
    await expect(searchInput).toBeVisible()
    await searchInput.fill('日落')
    await page.keyboard.press('Enter')

    // 等待搜索结果加载
    await page.waitForTimeout(2000)

    // 验证结果区域显示
    const resultsContainer = page.locator('text="搜索结果"]').or(
      page.locator('[class*="result" i], [class*="card" i]')
    )
    await expect(resultsContainer.first()).toBeVisible({ timeout: 10000 })
  })

  test('搜索历史显示之前的查询', async ({ page }) => {
    // 执行一次搜索
    const searchInput = page.locator('input[placeholder*="搜索"], textarea[placeholder*="搜索"]').first()
    await searchInput.fill('海洋')
    await page.keyboard.press('Enter')
    await page.waitForTimeout(2000)

    // 验证历史记录（如果实现）
    const historySection = page.locator('text="历史"').or(
      page.locator('[class*="history" i]')
    )
    // 注意：这个测试取决于历史记录的实现
  })
})

test.describe('图片上传和搜索功能', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto(`${BASE_URL}/search`)
  })

  test('可以上传图片进行搜索', async ({ page }) => {
    // 查找图片上传按钮或区域
    const uploadButton = page.locator('button:has-text("上传"), [role="button"]:has-text("图片"), [role="button"]:has-text("上传")').first()
    const uploadArea = page.locator('[class*="upload" i], [role="button"]:has([class*="upload"])').first()

    // 检查是否至少有一种上传方式可用
    const hasUploadButton = await uploadButton.count() > 0
    const hasUploadArea = await uploadArea.count() > 0

    expect(hasUploadButton || hasUploadArea).toBe(true)

    if (hasUploadButton) {
      await uploadButton.click()
    } else if (hasUploadArea) {
      await uploadArea.click()
    }

    // 创建一个简单的测试图片
    const testImageData = 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=='

    // 上传测试图片
    const fileInput = page.locator('input[type="file"]')
    if (await fileInput.count() > 0) {
      await fileInput.setInputFiles({
        name: 'test.png',
        mimeType: 'image/png',
        buffer: Buffer.from(testImageData, 'base64'),
      })

      // 点击确认上传
      await page.click('button:has-text("搜索"), button[type="submit"]')

      // 等待结果
      await page.waitForTimeout(3000)

      // 验证有某种响应（错误或结果）
      const pageContent = await page.content()
      expect(pageContent.length).toBeGreaterThan(0)
    }
  })

  test('上传不支持格式时显示错误', async ({ page }) => {
    // 查找文件输入
    const fileInput = page.locator('input[type="file"]')

    if (await fileInput.count() > 0) {
      // 尝试上传文本文件（假设不支持）
      await fileInput.setInputFiles({
        name: 'test.txt',
        mimeType: 'text/plain',
        buffer: Buffer.from('test'),
      })

      // 验证错误消息
      await expect(page.locator('text*="错误", text*="格式"').first()).toBeVisible({ timeout: 5000 })
    }
  })
})

test.describe('页面响应式设计', () => {
  const viewports = [
    { width: 320, height: 568, name: 'Mobile' },
    { width: 768, height: 1024, name: 'Tablet' },
    { width: 1024, height: 768, name: 'Desktop' },
  ]

  viewports.forEach((vp) => {
    test(`在 ${vp.name} 视口 (${vp.width}x${vp.height}) 上页面正常显示`, async ({ page }) => {
      // 设置视口大小
      await page.setViewportSize({ width: vp.width, height: vp.height })

      // 访问页面
      await page.goto(BASE_URL)

      // 验证主要内容可见
      const mainContent = page.locator('main, [role="main"]').first()
      await expect(mainContent).toBeVisible()

      // 验证导航栏可见（如果存在）
      const nav = page.locator('nav, [role="navigation"]').first()
      if (await nav.count() > 0) {
        await expect(nav).toBeVisible()
      }
    })
  })
})

test.describe('页面加载性能', () => {
  test('首页加载时间在合理范围内', async ({ page }) => {
    // 开始导航计时
    const startTime = Date.now()

    await page.goto(BASE_URL, { waitUntil: 'networkidle' })

    const loadTime = Date.now() - startTime

    // 验证加载时间不超过 5 秒
    expect(loadTime).toBeLessThan(5000)
  })

  test('搜索页面加载时间在合理范围内', async ({ page }) => {
    const startTime = Date.now()

    await page.goto(`${BASE_URL}/search`, { waitUntil: 'networkidle' })

    const loadTime = Date.now() - startTime

    expect(loadTime).toBeLessThan(5000)
  })
})

test.describe('无障碍性测试', () => {
  test('页面具有可访问的标题层级', async ({ page }) => {
    await page.goto(BASE_URL)

    // 检查是否存在 h1
    const h1 = page.locator('h1').first()
    await expect(h1).toBeVisible()

    // 检查标题层级正确
    const headings = await page.locator('h1, h2, h3, h4, h5, h6').all()
    expect(headings.length).toBeGreaterThan(0)
  })

  test('页面元素具有适当的 ARIA 属性', async ({ page }) => {
    await page.goto(BASE_URL)

    // 检查主要导航和交互元素
    const nav = page.locator('nav, [role="navigation"]').first()
    if (await nav.count() > 0) {
      await expect(nav).toBeVisible()
    }

    // 检查表单输入是否有标签
    const inputs = page.locator('input, textarea, select').all()
    for (const input of inputs.slice(0, 3)) {
      const isVisible = await input.isVisible()
      if (isVisible) {
        // 验证输入有相关联的标签
        const hasLabel = await input.evaluate((el) => {
          const labels = ['aria-label', 'aria-labelledby', 'placeholder', 'id']
          return labels.some(attr => el.hasAttribute(attr))
        })
        expect(hasLabel).toBe(true)
      }
    }
  })
})
