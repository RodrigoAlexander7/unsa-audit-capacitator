import { describe, expect, it } from 'vitest';
import { fetchHealth } from './health';

const jsonResponse = (body: unknown, status = 200) =>
	Promise.resolve(new Response(JSON.stringify(body), { status }));

describe('fetchHealth (AC-001-6)', () => {
	it('reporta api y base de datos arriba', async () => {
		const fakeFetch = (() => jsonResponse({ status: 'ok', database: 'up' })) as typeof fetch;
		expect(await fetchHealth(fakeFetch, 'http://api')).toEqual({ api: 'up', database: 'up' });
	});

	it('reporta base de datos caida cuando la API responde 503', async () => {
		const fakeFetch = (() =>
			jsonResponse({ status: 'degraded', database: 'down' }, 503)) as typeof fetch;
		expect(await fetchHealth(fakeFetch, 'http://api')).toEqual({ api: 'up', database: 'down' });
	});

	it('reporta api caida si la peticion falla', async () => {
		const fakeFetch = (() => Promise.reject(new Error('ECONNREFUSED'))) as typeof fetch;
		expect(await fetchHealth(fakeFetch, 'http://api')).toEqual({
			api: 'down',
			database: 'unknown'
		});
	});
});
