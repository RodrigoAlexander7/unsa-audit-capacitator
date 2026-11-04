export type ApiStatus = {
	api: 'up' | 'down';
	database: 'up' | 'down' | 'unknown';
};

/** Consulta GET /health del backend. Nunca lanza: si falla, la API se considera caida. */
export async function fetchHealth(fetchFn: typeof fetch, baseUrl: string): Promise<ApiStatus> {
	try {
		const response = await fetchFn(`${baseUrl}/health`);
		const body = (await response.json()) as { database?: string };
		const database = body.database === 'up' || body.database === 'down' ? body.database : 'unknown';
		return { api: 'up', database };
	} catch {
		return { api: 'down', database: 'unknown' };
	}
}
