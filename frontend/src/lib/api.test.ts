import { describe, expect, it } from 'vitest';
import { apiGet, errorMessage } from './api';

describe('apiGet', () => {
	it('envia el token como Bearer y devuelve los datos', async () => {
		let seen: Headers | undefined;
		const fakeFetch = ((_url: string, init?: RequestInit) => {
			seen = new Headers(init?.headers);
			return Promise.resolve(new Response(JSON.stringify({ ok: 1 }), { status: 200 }));
		}) as unknown as typeof fetch;
		const result = await apiGet<{ ok: number }>(fakeFetch, 'http://api', '/me', 'abc');
		expect(seen?.get('Authorization')).toBe('Bearer abc');
		expect(result).toEqual({ status: 200, data: { ok: 1 } });
	});

	it('devuelve el status y sin datos cuando el API responde error', async () => {
		const fakeFetch = (() => Promise.resolve(new Response('{}', { status: 401 }))) as typeof fetch;
		expect(await apiGet(fakeFetch, 'http://api', '/me', null)).toEqual({
			status: 401,
			data: null
		});
	});

	it('devuelve status 0 si no hay conexion', async () => {
		const fakeFetch = (() => Promise.reject(new Error('down'))) as typeof fetch;
		expect(await apiGet(fakeFetch, 'http://api', '/me', null)).toEqual({
			status: 0,
			data: null
		});
	});
});

describe('errorMessage', () => {
	it('usa detail string, lista de validacion o el fallback', () => {
		expect(errorMessage({ detail: 'Email no disponible' }, 'x')).toBe('Email no disponible');
		expect(errorMessage({ detail: [{ msg: 'too short' }] }, 'x')).toBe(
			'Revisa los datos ingresados.'
		);
		expect(errorMessage(null, 'fallback')).toBe('fallback');
	});
});
