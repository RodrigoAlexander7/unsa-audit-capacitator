import { describe, expect, it } from 'vitest';
import { renderMarkdown } from './markdown';

describe('renderMarkdown', () => {
	it('renderiza titulos, tablas y enlaces internos', () => {
		const html = renderMarkdown(
			'# Titulo\n\n| a | b |\n|---|---|\n| 1 | 2 |\n\n[ROF](/documents/rof)'
		);
		expect(html).toContain('<h1>Titulo</h1>');
		expect(html).toContain('<table>');
		expect(html).toContain('<a href="/documents/rof">ROF</a>');
	});

	it('escapa el HTML crudo (bloques y en linea)', () => {
		const block = renderMarkdown('<script>alert(1)</script>');
		expect(block).not.toContain('<script>');
		expect(block).toContain('&lt;script&gt;');
		const inline = renderMarkdown('texto <img src=x onerror=alert(1)> fin');
		expect(inline).not.toContain('<img');
	});

	it('elimina enlaces con esquemas peligrosos pero conserva el texto', () => {
		const html = renderMarkdown('[clic](javascript:alert(1)) y [datos](data:text/html;base64,AAA)');
		expect(html).not.toContain('href');
		expect(html).toContain('clic');
	});

	it('permite https, mailto y anclas, y no carga imagenes remotas', () => {
		expect(renderMarkdown('[x](https://example.com)')).toContain('href="https://example.com"');
		expect(renderMarkdown('[x](mailto:a@b.c)')).toContain('href="mailto:a@b.c"');
		expect(renderMarkdown('[x](#seccion)')).toContain('href="#seccion"');
		expect(renderMarkdown('![alt](https://example.com/p.png)')).not.toContain('<img');
		expect(renderMarkdown('[x](//evil.example)')).not.toContain('href');
	});
});
