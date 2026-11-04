import AxeBuilder from '@axe-core/playwright';
import type { Page } from '@playwright/test';
import { expect, loginDemo, loginSuperadmin, test } from './support';

// AC-008-5: sin violaciones serias o críticas en las páginas principales.
async function expectAccessible(page: Page) {
	const results = await new AxeBuilder({ page })
		.withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa'])
		.analyze();
	const blocking = results.violations.filter(
		(v) => v.impact === 'serious' || v.impact === 'critical'
	);
	expect(
		blocking.map((v) => `${v.id}: ${v.help} (${v.nodes.length}) ${v.nodes[0]?.target.join(' ')}`)
	).toEqual([]);
}

test('login', async ({ page }) => {
	await page.goto('/login');
	await expectAccessible(page);
});

test('rutas del participante', async ({ page }) => {
	await loginDemo(page);
	await page.goto('/routes');
	await expect(page.getByTestId('route-sensibilizacion')).toBeVisible();
	await expectAccessible(page);
});

test('módulo con ejercicio', async ({ page }) => {
	await loginDemo(page);
	await page.goto('/routes/sensibilizacion');
	await page.getByTestId('module-5').getByRole('link').click();
	await expect(page.getByTestId('lesson')).toBeVisible();
	await expectAccessible(page);
});

test('matriz PIMS', async ({ page }) => {
	await loginDemo(page);
	await page.goto('/documents/pims');
	await expect(page.getByTestId('pims-table')).toBeVisible();
	await expectAccessible(page);
});

test('panel del superadmin', async ({ page }) => {
	await loginSuperadmin(page);
	await page.goto('/admin');
	await expect(page.getByTestId('routes-table')).toBeVisible();
	await expectAccessible(page);
});
