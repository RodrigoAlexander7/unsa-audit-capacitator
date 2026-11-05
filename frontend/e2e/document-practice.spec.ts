import AxeBuilder from '@axe-core/playwright';
import { execFileSync } from 'node:child_process';
import { resolve } from 'node:path';
import type { Page } from '@playwright/test';
import { expect, loginDemo, ROOT, test } from './support';

const BACKEND_DIR = resolve(ROOT, 'backend');
const TEMP_SLUG = 'e2e-doc-alcance';

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

function runBackendPy(script: string, arg = ''): string {
	return execFileSync('uv', ['run', 'python', '-c', script, arg], {
		cwd: BACKEND_DIR,
		encoding: 'utf-8'
	}).trim();
}

const TEMP_SPEC = {
	prompt: 'Redacta la ficha de alcance del PIMS para un servicio universitario ficticio.',
	scenario:
		'La UNSA ficticia delimita el PIMS de matrícula y atención estudiantil bajo responsabilidad de la Oficina de Protección de Datos.',
	document_title: 'Alcance del PIMS (ejercicio temporal E2E)',
	sections: [
		{
			id: 'sec-meta',
			title: 'Aprobación y vigencia',
			fields: [
				{
					id: 'approved_by',
					label: 'Cargo que aprueba el alcance',
					type: 'position',
					required: true,
					options: [
						{ id: 'rector', label: 'Rectorado' },
						{ id: 'dpo', label: 'Oficial de Datos Personales' }
					],
					validation: {
						accepted: ['rector'],
						feedback_error: 'Solo la Alta Dirección (Rectorado) aprueba el alcance institucional.'
					}
				},
				{
					id: 'owner_position',
					label: 'Responsable de mantener el documento',
					type: 'position',
					required: true,
					options: [
						{ id: 'rector', label: 'Rectorado' },
						{ id: 'dpo', label: 'Oficial de Datos Personales' }
					],
					validation: {
						exact: 'dpo',
						feedback_error:
							'El mantenimiento operativo del alcance corresponde al Oficial de Datos.'
					}
				},
				{
					id: 'approval_date',
					label: 'Fecha de aprobación',
					type: 'date',
					required: true,
					validation: { min_date: '2026-01-01', max_date: '2026-12-31' }
				},
				{
					id: 'review_date',
					label: 'Fecha de próxima revisión',
					type: 'date',
					required: true,
					validation: { min_date: '2026-01-01', max_date: '2028-12-31' }
				}
			]
		},
		{
			id: 'sec-scope',
			title: 'Límites, sistemas y justificación',
			fields: [
				{
					id: 'included_systems',
					label: 'Sistemas dentro del alcance',
					type: 'multiselect',
					required: true,
					options: [
						{ id: 'matricula', label: 'Sistema Académico y Matrícula' },
						{ id: 'portal', label: 'Portal de Transparencia' }
					],
					validation: {
						exact_ids: ['matricula'],
						feedback_error: 'Incluye el sistema con tratamiento de matrícula estudiantil.'
					}
				},
				{
					id: 'exclusions_justification',
					label: 'Justificación de inclusiones y exclusiones',
					type: 'textarea',
					required: true,
					validation: {
						rubric: {
							min_words: 15,
							forbidden_any: [
								{
									phrases: ['por costo', 'muy caro'],
									feedback: 'Nunca se justifica una exclusión por costo económico.'
								}
							],
							criteria: [
								{
									id: 'crit-inter',
									label: 'Interfaces con sistemas fuera de alcance',
									keywords_any: ['interfaz', 'transferencia', 'flujo'],
									feedback_missing:
										'Explica las interfaces o transferencias en la frontera del alcance.'
								},
								{
									id: 'crit-titular',
									label: 'Rol como responsable y protección al titular',
									keywords_any: ['responsable', 'titular', 'estudiante'],
									feedback_missing: 'Menciona el rol respecto al titular o estudiante.'
								}
							]
						}
					}
				}
			]
		}
	],
	cross_rules: [
		{
			id: 'rule-disjoint-approval',
			kind: 'disjoint',
			fields: ['approved_by', 'owner_position'],
			feedback: 'Quien aprueba el alcance no debe coincidir con quien lo mantiene operativamente.'
		},
		{
			id: 'rule-date-order',
			kind: 'date_order',
			fields: ['approval_date', 'review_date'],
			params: { min_days: 30 },
			feedback: 'La próxima revisión debe fijarse al menos 30 días después de aprobar.'
		}
	]
};

test.describe('Práctica documental (F8)', () => {
	let tempModuleId = '';

	test.beforeAll(() => {
		const insertPy = `
import asyncio, json, sys
from sqlalchemy import delete
from unsa_audit.core.config import get_settings
from unsa_audit.core.database import create_engine, create_session_factory
from unsa_audit.learning.infrastructure.content_loader import module_id
from unsa_audit.learning.infrastructure.models import ModuleModel

spec = json.loads(sys.argv[1])
mid = module_id("sensibilizacion", "${TEMP_SLUG}")

async def main():
    eng = create_engine(get_settings().database_url)
    sf = create_session_factory(eng)
    async with sf() as s:
        await s.execute(delete(ModuleModel).where(ModuleModel.id == mid))
        s.add(ModuleModel(
            id=mid,
            route_code="sensibilizacion",
            slug="${TEMP_SLUG}",
            order=99,
            title="Práctica documental temporal (Alcance UNSA)",
            minutes=15,
            mandatory=False,
            is_final=False,
            planned=False,
            lesson_md="## Alcance del PIMS\\n\\nDelimita sistemas, fronteras y aprobación.",
            reference_title="Ejemplo resuelto UNSA — Alcance de Matrícula",
            reference_md="## Modelo de referencia\\n\\n- Aprobado por Rectorado\\n- Mantenido por Oficial de Datos",
            exercise_kind="document_form",
            exercise_spec=spec,
            exercise_generator=None,
            exercise_params={},
            pass_score=70,
        ))
        await s.commit()
    await eng.dispose()
    print(str(mid))

asyncio.run(main())
`;
		tempModuleId = runBackendPy(insertPy, JSON.stringify(TEMP_SPEC));
	});

	test.afterAll(() => {
		const cleanupPy = `
import asyncio
from sqlalchemy import delete
from unsa_audit.core.config import get_settings
from unsa_audit.core.database import create_engine, create_session_factory
from unsa_audit.learning.infrastructure.content_loader import module_id
from unsa_audit.learning.infrastructure.models import ModuleModel

mid = module_id("sensibilizacion", "${TEMP_SLUG}")

async def main():
    eng = create_engine(get_settings().database_url)
    sf = create_session_factory(eng)
    async with sf() as s:
        await s.execute(delete(ModuleModel).where(ModuleModel.id == mid))
        await s.commit()
    await eng.dispose()

asyncio.run(main())
`;
		runBackendPy(cleanupPy);
	});

	test('R3 SoA muestra ejemplo resuelto lado a lado y pasa axe-core', async ({ page }) => {
		await loginDemo(page);
		await page.goto('/routes/implementacion');
		await page.getByRole('link', { name: /Declaración de aplicabilidad/i }).click();

		await expect(page.getByTestId('practice-side-by-side')).toBeVisible();
		await expect(page.getByTestId('reference-panel')).toContainText('Biblioteca Central');
		await expectAccessible(page);

		const toggle = page.getByRole('button', { name: 'Ocultar' });
		await toggle.click();
		await expect(page.getByRole('button', { name: 'Mostrar' })).toHaveAttribute(
			'aria-expanded',
			'false'
		);
	});

	test('R2 completa muestra los 8 módulos reales con referencia y pasa axe-core', async ({
		page
	}) => {
		await loginDemo(page);
		await page.goto('/routes/interpretacion');
		await expect(page.getByText('Próximamente')).toHaveCount(0);

		await page
			.getByRole('link', { name: /Contexto de la organización y alcance del PIMS/i })
			.click();
		await expect(page.getByTestId('practice-side-by-side')).toBeVisible();
		await expect(page.getByTestId('reference-panel')).toContainText('Registros Académicos');
		await expectAccessible(page);

		await page.goto('/routes/interpretacion');
		await page.getByRole('link', { name: /Riesgos de privacidad/i }).click();
		await expect(page.getByTestId('risk-scenario')).toBeVisible();
		await expect(page.getByTestId('practice-side-by-side')).toBeVisible();
		await expectAccessible(page);
	});

	test('R3 completa muestra los 9 módulos reales (tratamiento y no conformidades) y pasa axe-core', async ({
		page
	}) => {
		await loginDemo(page);
		await page.goto('/routes/implementacion');
		await expect(page.getByText('Próximamente')).toHaveCount(0);

		await page.getByRole('link', { name: /Plan de tratamiento y recursos/i }).click();
		await expect(page.getByTestId('treatment-scenario')).toBeVisible();
		await expect(page.getByTestId('practice-side-by-side')).toBeVisible();
		await expectAccessible(page);

		await page.goto('/routes/implementacion');
		await page.getByRole('link', { name: /Evidencias y registros/i }).click();
		await expect(page.getByTestId('nc-scenario')).toBeVisible();
		await expect(page.getByTestId('practice-side-by-side')).toBeVisible();
		await expectAccessible(page);
	});

	test('document_form valida reglas cruzadas, muestra guía al 3er fallo, aprueba y pasa axe-core', async ({
		page
	}) => {
		await page.goto('/register');
		await page.getByLabel('Nombre completo').fill('Auditor Documental E2E');
		await page
			.getByLabel('Correo electrónico')
			.fill(`e2e-doc-${Date.now()}-${Math.floor(Math.random() * 1e6)}@e2e.unsa.example`);
		await page.getByLabel('Contraseña').fill('E2e-password-1');
		await page.getByRole('button', { name: 'Registrarme' }).click();
		await expect(page.getByTestId('session-user')).toHaveText('Auditor Documental E2E');

		await page.goto('/routes/sensibilizacion');
		await page.getByRole('button', { name: 'Matricularme' }).click();
		await page.goto(`/routes/sensibilizacion/${tempModuleId}`);

		await expect(page.getByTestId('practice-side-by-side')).toBeVisible();
		await expect(page.getByTestId('reference-panel')).toContainText('Rectorado');

		const submit = page.getByRole('button', { name: /Enviar/ });
		await expect(submit).toBeDisabled();

		// Rellena con errores deliberados: autoaprobación, fecha revisión anterior y excusa por costo.
		await page.getByLabel(/Cargo que aprueba el alcance/i).selectOption('dpo');
		await page.getByLabel(/Responsable de mantener el documento/i).selectOption('dpo');
		await page.getByLabel(/Fecha de aprobación/i).fill('2026-06-01');
		await page.getByLabel(/Fecha de próxima revisión/i).fill('2026-05-01');
		await page.getByRole('checkbox', { name: /Sistema Académico y Matrícula/i }).check();
		await page
			.getByLabel(/Justificación de inclusiones y exclusiones/i)
			.fill('Excluimos otros sistemas por costo alto de implementación inmediata.');

		await expect(submit).toBeEnabled();
		await submit.click();

		await expect(page.getByTestId('attempt-result')).toHaveAttribute('data-passed', 'false');
		await expect(page.getByTestId('attempt-result')).toContainText('Intento 1');
		await expect(page.getByTestId('doc-cross-rules')).toContainText('no debe coincidir');
		await expect(page.getByRole('alert').first()).toBeVisible();
		await expect(page.getByTestId('solution-guide')).toHaveCount(0);
		await expectAccessible(page);

		// 2do intento fallido: aún sin guía
		await submit.click();
		await expect(page.getByTestId('attempt-result')).toContainText('Intento 2');
		await expect(page.getByTestId('solution-guide')).toHaveCount(0);

		// 3er intento fallido: no aprueba automáticamente y muestra guía de solución
		await submit.click();
		await expect(page.getByTestId('attempt-result')).toContainText('Intento 3');
		await expect(page.getByTestId('attempt-result')).toHaveAttribute('data-passed', 'false');
		await expect(page.getByTestId('solution-guide')).toBeVisible();
		await expectAccessible(page);

		// Corrige siguiendo la guía y aprueba con 100 %
		await page.getByLabel(/Cargo que aprueba el alcance/i).selectOption('rector');
		await page.getByLabel(/Fecha de próxima revisión/i).fill('2026-12-01');
		await page
			.getByLabel(/Justificación de inclusiones y exclusiones/i)
			.fill(
				'La UNSA actúa como responsable del tratamiento de matrícula estudiantil y controla toda interfaz y transferencia hacia sistemas administrativos externos.'
			);

		await submit.click();
		await expect(page.getByTestId('attempt-result')).toHaveAttribute('data-passed', 'true');
		await expect(page.getByTestId('attempt-result')).toContainText('100 %');
	});
});
