import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import type { Page } from '@playwright/test';
import { expect, loginDemo, loginSuperadmin, ROOT, test } from './support';

const readJson = (relative: string) =>
	JSON.parse(readFileSync(resolve(ROOT, 'content', relative), 'utf-8'));

// AC-008-4: recorrido principal del participante y del superadmin.

/** Registra una cuenta @e2e.unsa.example (`--reset-demo` las elimina) y deja la sesión abierta. */
async function registerE2e(page: Page): Promise<void> {
	await page.goto('/register');
	await page.getByLabel('Nombre completo').fill('Participante E2E');
	await page
		.getByLabel('Correo electrónico')
		.fill(`e2e-${Date.now()}-${Math.floor(Math.random() * 1e6)}@e2e.unsa.example`);
	await page.getByLabel('Contraseña').fill('E2e-password-1');
	await page.getByRole('button', { name: 'Registrarme' }).click();
	await expect(page.getByTestId('session-user')).toHaveText('Participante E2E');
}

test('registro → matrícula → módulo con ejercicio → resultado', async ({ page }) => {
	await registerE2e(page);

	await page.goto('/routes/sensibilizacion');
	await page.getByRole('button', { name: 'Matricularme' }).click();
	await expect(page.getByTestId('module-5')).toBeVisible();

	// Módulo 5 (quiz estático): primero una respuesta incompleta/errónea, luego la correcta.
	await page.getByTestId('module-5').getByRole('link').click();
	await expect(page.getByTestId('lesson')).toBeVisible();
	const quiz = readJson('routes/1-sensibilizacion/05-cambios-y-trazabilidad.exercise.json').spec;
	const pick = async (answerFor: (q: { correct: string; options: { id: string }[] }) => string) => {
		for (const question of quiz.questions) {
			await page.locator(`input[name="q-${question.id}"][value="${answerFor(question)}"]`).check();
		}
		await page.getByRole('button', { name: /Enviar/ }).click();
	};

	await pick((q) => q.options.find((o) => o.id !== q.correct)!.id);
	await expect(page.getByTestId('attempt-result')).toHaveAttribute('data-passed', 'false');

	await pick((q) => q.correct);
	await expect(page.getByTestId('attempt-result')).toHaveAttribute('data-passed', 'true');
	await expect(page.getByTestId('attempt-result')).toContainText('100 %');

	await page.goto('/routes');
	await expect(page.getByTestId('route-sensibilizacion')).toContainText('En curso');
});

test('el participante demo entra y ve sus rutas', async ({ page }) => {
	await loginDemo(page);
	await page.goto('/routes');
	await expect(page.getByRole('heading', { name: 'Mis rutas de capacitación' })).toBeVisible();
	await expect(page.getByTestId('route-sensibilizacion')).toContainText('Aprobada');
	await expect(page.getByTestId('total-hours')).not.toHaveText('0 h');
});

test('un participante no accede al panel del superadmin', async ({ page }) => {
	await loginDemo(page);
	await expect(page.getByTestId('admin-link')).toHaveCount(0);
	await page.goto('/admin');
	await expect(page).not.toHaveURL(/\/admin/);
	await expect(page.getByRole('heading', { name: 'Panel del superadmin' })).toHaveCount(0);
});

test('el superadmin ve estadísticas del cohorte demo', async ({ page }) => {
	await loginSuperadmin(page);
	await page.getByTestId('admin-link').click();
	await expect(page.getByRole('heading', { name: 'Panel del superadmin' })).toBeVisible();

	const r1 = page.getByTestId('stats-sensibilizacion');
	await expect(r1).toBeVisible();
	await expect(page.getByTestId('hardest')).toBeVisible();
	await expect(page.getByTestId('assessment-controller')).toBeVisible();
	await expect(page.getByTestId('assessment-processor')).toBeVisible();
	await expect(page.getByTestId('pims-summary')).toContainText('vigentes');

	await page.goto('/admin/advisor');
	await expect(page.getByRole('heading', { level: 1 })).toBeVisible();
});

test('documentos: diferencias entre versiones y matriz PIMS', async ({ page }) => {
	await loginDemo(page);
	await page.goto('/documents/rof');
	await expect(page.getByTestId('current-version')).toBeVisible();

	await page.goto('/documents/rof/diff?from=1&to=2');
	await expect(page.getByTestId('diff-title')).toHaveText('v1 → v2');

	await page.goto('/documents/pims');
	await expect(page.getByTestId('completeness')).toContainText('de 11 vigentes');
	await expect(page.getByTestId('pims-table').locator('tbody tr')).toHaveCount(11);
});

test('evaluación controller completa hasta ver resultados por competencia', async ({ page }) => {
	await registerE2e(page);
	await page.goto('/assessment');
	await page.getByTestId('profile-controller').getByRole('button').click();
	await expect(page).toHaveURL(/\/assessment\/[0-9a-f-]{36}/);
	await page.waitForLoadState('networkidle'); // espera la hidratación antes de marcar opciones

	const bank = readJson('assessment/controller.json');
	const correct = new Map<string, string>(
		bank.questions.map((q: { id: string; correct: string }) => [q.id, q.correct])
	);
	for (const id of correct.keys()) {
		await page.locator(`input[name="q-${id}"][value="${correct.get(id)}"]`).check();
	}
	await expect(page.getByTestId('answered')).toContainText('12/12');
	await page.getByRole('button', { name: 'Enviar evaluación' }).click();

	await expect(page.getByTestId('assessment-result')).toContainText('100 %');
	await expect(page.getByTestId('competencies')).toBeVisible();
	await expect(page.getByTestId('requirements')).toBeVisible();
});
