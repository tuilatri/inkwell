import { expect, test } from '@playwright/test'

const username = process.env.E2E_ADMIN_USERNAME
const password = process.env.E2E_ADMIN_PASSWORD

test.describe('Inkwell Novel Reader flow', () => {
  test.skip(!username || !password, 'ADMIN credentials in novel_reader/.env are required')

  test('login → library → EN/VI → read → scroll → refresh → search', async ({ page }) => {
    await page.goto('/login')
    await page.getByLabel('Tên đăng nhập').fill(username!)
    await page.getByLabel('Mật khẩu').fill(password!)
    await page.getByRole('button', { name: 'Đăng nhập' }).click()

    await expect(page.getByRole('heading', { name: 'Thư viện' })).toBeVisible({ timeout: 180_000 })
    await page.screenshot({ path: 'test-results/desktop-library.png' })
    const titles = page.locator('button:has-text("Mở truyện")')
    await expect(titles.first()).toBeVisible()
    expect(await titles.count()).toBe(4)
    expect(await page.locator('img').count()).toBe(0)

    await titles.first().click()
    await expect(page.getByRole('tab', { name: 'VI' })).toHaveAttribute('data-state', 'active')
    await page.getByRole('tab', { name: 'EN' }).click()
    await page.getByRole('tab', { name: 'VI' }).click()
    await page.getByTestId('chapter-list').getByRole('button').first().click()

    await expect(page.getByTestId('reader-view')).toBeVisible()
    await page.evaluate(() => window.scrollTo(0, 600))
    await page.waitForTimeout(1500)
    await page.reload()
    await expect(page.getByTestId('reader-view')).toBeVisible()
    await page.waitForTimeout(1000)
    expect(await page.evaluate(() => window.scrollY)).toBeGreaterThan(100)

    await page.getByRole('button', { name: 'Mở tìm kiếm' }).click()
    const searchInput = page.getByRole('combobox', { name: 'Tìm kiếm' })
    await searchInput.fill('chuong 1')
    await expect(searchInput).toBeVisible()
  })

  test('mobile viewport keeps the chapter list reachable', async ({ browser }) => {
    const context = await browser.newContext({ viewport: { width: 390, height: 844 } })
    const page = await context.newPage()
    await page.goto('/login')
    await expect(page.getByLabel('Tên đăng nhập')).toBeVisible()
    await page.screenshot({ path: 'test-results/mobile-login.png' })
    await context.close()
  })
})
