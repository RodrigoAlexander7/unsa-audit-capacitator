import { describe, expect, it } from 'vitest';
import { detectAssistantContext } from './types';

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
