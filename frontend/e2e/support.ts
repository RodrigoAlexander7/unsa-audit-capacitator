import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { expect, test as base, type Page } from '@playwright/test';

/**
 * `goto` espera a que la red quede inactiva: así la hidratación de Svelte termina antes de
 * rellenar formularios (si no, la hidratación puede borrar lo escrito en campos controlados).
 */
export const test = base.extend({
	page: async ({ page }, use) => {
		const goto = page.goto.bind(page);
		page.goto = (url, options) => goto(url, { waitUntil: 'networkidle', ...options });
		await use(page);
	}
});
export { expect };

export const ROOT = resolve(import.meta.dirname, '../..');
export const DEMO_PASSWORD = 'Demo-1234';
export const DEMO_EMAIL = 'ana.quispe@demo.unsa.example';
export const DEMO_RECENT = 'elena.medina@demo.unsa.example'; // matriculada, sin intentos

/** Lee variables de ../.env (no se versiona); las del entorno tienen prioridad. */
function readEnv(): Record<string, string> {
	const values: Record<string, string> = {};
	try {
		for (const line of readFileSync(resolve(ROOT, '.env'), 'utf-8').split('\n')) {
			const match = line.match(/^\s*([A-Z_]+)\s*=\s*(.*)\s*$/);
			if (match) values[match[1]] = match[2];
		}
	} catch {
		// sin .env: se usan los valores del entorno o los del ejemplo
	}
	return values;
}

const env = readEnv();
export const SUPERADMIN_EMAIL =
	process.env.SUPERADMIN_EMAIL ?? env.SUPERADMIN_EMAIL ?? 'superadmin@unsa-poc.example';
export const SUPERADMIN_PASSWORD =
	process.env.SUPERADMIN_PASSWORD ?? env.SUPERADMIN_PASSWORD ?? 'change-me-superadmin-dev';

export async function login(page: Page, email: string, password: string): Promise<void> {
	await page.goto('/login');
	await page.getByLabel('Correo electrónico').fill(email);
	await page.getByLabel('Contraseña').fill(password);
	await page.getByRole('button', { name: 'Entrar' }).click();
	await expect(page.getByTestId('session-user')).toBeVisible();
}

export const loginDemo = (page: Page, email = DEMO_EMAIL) => login(page, email, DEMO_PASSWORD);
export const loginSuperadmin = (page: Page) => login(page, SUPERADMIN_EMAIL, SUPERADMIN_PASSWORD);
