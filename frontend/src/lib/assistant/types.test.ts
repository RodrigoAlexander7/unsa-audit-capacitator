import { describe, expect, it } from 'vitest';
import { detectAssistantContext, resolveAliasesInText } from './types';

describe('detectAssistantContext', () => {
	it('detecta el modulo actual cuando navega dentro de una ruta', () => {
		const ctx = detectAssistantContext('/routes/interpretacion/1111-2222', {
			code: 'interpretacion',
			module: '1111-2222'
		});
		expect(ctx.moduleId).toBe('1111-2222');
		expect(ctx.routePath).toBe('/routes/interpretacion/1111-2222');
		expect(ctx.label).toContain('módulo');
		expect(ctx.suggestions.length).toBeGreaterThanOrEqual(2);
	});

	it('detecta contexto documental sin moduleId en /documents', () => {
		const ctx = detectAssistantContext('/documents/pims-alcance', { code: 'pims-alcance' });
		expect(ctx.moduleId).toBeNull();
		expect(ctx.label).toContain('documentos');
	});

	it('ofrece contexto general de UNSA y PIMS en otras paginas', () => {
		const ctx = detectAssistantContext('/university', {});
		expect(ctx.moduleId).toBeNull();
		expect(ctx.label).toContain('UNSA');
	});
});

describe('resolveAliasesInText', () => {
	const aliases = [
		{
			alias: 'P-01',
			full_name: 'Ana Quispe',
			email: 'ana@demo.unsa.example',
			stalled: false,
			overall_progress_pct: 90
		},
		{
			alias: 'P-02',
			full_name: 'Carmen Delgado',
			email: 'carmen@demo.unsa.example',
			stalled: true,
			overall_progress_pct: 40
		}
	];

	it('resuelve localmente cada P-xx al nombre real del participante', () => {
		const out = resolveAliasesInText(
			'P-02 está estancada mientras P-01 completó la ruta.',
			aliases
		);
		expect(out).toBe(
			'**Carmen Delgado** (P-02) está estancada mientras **Ana Quispe** (P-01) completó la ruta.'
		);
	});

	it('evita duplicar nombres si el alias ya aparece resuelto', () => {
		const out = resolveAliasesInText('**Carmen Delgado** (P-02) requiere seguimiento.', aliases);
		expect(out).toBe('**Carmen Delgado** (P-02) requiere seguimiento.');
	});
});
