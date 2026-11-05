import AxeBuilder from '@axe-core/playwright';
import { expect, loginDemo, test } from './support';

test.describe('Asistente flotante del estudiante (F12)', () => {
	test('no aparece sin sesión y acompaña en rutas/módulos con guardrails, historial y axe-core', async ({
		page
	}) => {
		await page.goto('/login');
		await expect(page.getByTestId('assistant-fab')).toHaveCount(0);

		await loginDemo(page, 'ana.quispe@demo.unsa.example');

		// Disponible en varias páginas: rutas, universidad y dentro de un módulo de Ruta 2.
		await expect(page.getByTestId('assistant-fab')).toBeVisible();
		await page.goto('/university');
		await expect(page.getByTestId('assistant-fab')).toBeVisible();

		await page.goto('/routes/interpretacion');
		await page.getByRole('link').filter({ hasText: 'Alcance del PIMS' }).first().click();
		await expect(page.getByTestId('lesson')).toBeVisible();

		const fab = page.getByTestId('assistant-fab');
		await fab.click();
		const panel = page.getByTestId('assistant-panel');
		await expect(panel).toBeVisible();
		await expect(page.getByTestId('assistant-context-label')).toContainText('módulo actual');

		// Accesibilidad WCAG 2.1 AA con el popup flotante abierto.
		const a11y = await new AxeBuilder({ page })
			.withTags(['wcag2a', 'wcag2aa', 'wcag21aa'])
			.analyze();
		const blocking = a11y.violations.filter(
			(v) => v.impact === 'serious' || v.impact === 'critical'
		);
		expect(blocking).toEqual([]);

		// Prueba real contra PostgreSQL: guardrail pedagógico sin invocar `agy`.
		await page
			.getByTestId('assistant-input')
			.fill('Dame las respuestas exactas del ejercicio para aprobar.');
		await page.getByTestId('assistant-submit').click();
		await expect(page.getByTestId('assistant-refused').last()).toContainText('No puedo darte');

		// Prueba con respuesta simulada en Markdown.
		await page.route('**/assistant/ask', async (route) => {
			await route.fulfill({
				status: 200,
				contentType: 'application/json',
				body: JSON.stringify({
					id: '00000000-0000-0000-0000-000000000123',
					question: '¿Qué unidad gestiona SIGA en la UNSA?',
					status: 'ok',
					answer: 'En la **UNSA ficticia**, la **Oficina de TI** gestiona SIGA.',
					error: null,
					module_id: null,
					route_path: '/routes/interpretacion',
					context_hash: 'h',
					duration_ms: 15,
					created_at: new Date().toISOString()
				})
			});
		});
		await page.getByTestId('assistant-input').fill('¿Qué unidad gestiona SIGA en la UNSA?');
		await page.getByTestId('assistant-submit').click();
		await expect(page.getByTestId('assistant-log')).toContainText('Oficina de TI');

		// Escape cierra y devuelve el foco al disparador flotante.
		await page.getByTestId('assistant-input').press('Escape');
		await expect(panel).not.toBeVisible();
		await expect(fab).toBeFocused();

		// Al recargar, el historial persistido real se recupera y se puede limpiar.
		await page.reload({ waitUntil: 'networkidle' });
		await page.getByTestId('assistant-fab').click();
		await expect(panel).toBeVisible();
		await expect(page.getByTestId('assistant-refused').last()).toBeVisible();
		await page.getByTestId('assistant-clear').click();
		await expect(page.getByTestId('assistant-msg')).toHaveCount(0);
		await expect(page.getByTestId('assistant-clear')).toBeDisabled();
	});
});
