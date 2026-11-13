// FR11: repeated QA must navigate the real paginated oldest-first queue.
import { expect, type Page } from '@playwright/test';
export async function reviewCompany(page: Page, name: string) {
  const row = page.locator('.verification-company').filter({ hasText: name });
  await expect(page.locator('.verification-company').first()).toBeVisible();
  while ((await row.count()) === 0) {
    const next = page.getByRole('button', { name: 'Next', exact: true });
    await expect(next).toBeEnabled();
    const previousPage = await page.locator('.verification-pagination span').textContent();
    await next.click();
    await expect(page.locator('.verification-pagination span')).not.toHaveText(previousPage!);
    await expect(page.locator('.verification-company').first()).toBeVisible();
  }
  await row.getByRole('button', { name: 'Review', exact: true }).click();
}
