import { test, expect } from '@playwright/test'

test.describe('Code Review Assistant', () => {
  test('loads homepage with title', async ({ page }) => {
    await page.goto('/')
    await expect(page.getByRole('heading', { name: /Code Review/i })).toBeVisible()
    await expect(page.getByTestId('code-textarea')).toBeVisible()
  })

  test('shows demo mode badge', async ({ page }) => {
    await page.goto('/')
    await expect(page.getByTestId('inference-mode')).toHaveText('demo', { timeout: 15000 })
  })

  test('reviews code and shows side-by-side results', async ({ page }) => {
    await page.goto('/')
    await page.getByTestId('code-textarea').fill('def divide(a, b):\n    return a / b')
    await page.getByTestId('review-button').click()

    await expect(page.getByTestId('base-panel')).toBeVisible({ timeout: 15000 })
    await expect(page.getByTestId('finetuned-panel')).toBeVisible()

    const finetuned = page.getByTestId('finetuned-panel')
    await expect(finetuned.getByText(/division|zero/i).first()).toBeVisible()
  })

  test('example buttons populate code', async ({ page }) => {
    await page.goto('/')
    await page.getByRole('button', { name: 'SQL injection' }).click()
    await expect(page.getByTestId('code-textarea')).toContainText('SELECT')
  })

  test('disables review when code is empty', async ({ page }) => {
    await page.goto('/')
    await page.getByTestId('code-textarea').fill('')
    await expect(page.getByTestId('review-button')).toBeDisabled()
  })
})
