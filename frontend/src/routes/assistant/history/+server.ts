import { API_URL } from '$app/env/private';
import { json } from '@sveltejs/kit';
import type { RequestHandler } from './$types';

export const GET: RequestHandler = async ({ fetch, locals }) => {
	if (!locals.user || !locals.token) {
		return json({ detail: 'No autenticado' }, { status: 401 });
	}
	try {
		const response = await fetch(`${API_URL}/assistant/history`, {
			headers: { Authorization: `Bearer ${locals.token}` }
		});
		const parsed = await response.json().catch(() => null);
		return json(parsed ?? [], { status: response.status });
	} catch {
		return json({ detail: 'No se pudo cargar el historial.' }, { status: 502 });
	}
};

export const DELETE: RequestHandler = async ({ fetch, locals }) => {
	if (!locals.user || !locals.token) {
		return json({ detail: 'No autenticado' }, { status: 401 });
	}
	try {
		const response = await fetch(`${API_URL}/assistant/history`, {
			method: 'DELETE',
			headers: { Authorization: `Bearer ${locals.token}` }
		});
		const parsed = await response.json().catch(() => null);
		return json(parsed ?? { deleted: 0 }, { status: response.status });
	} catch {
		return json({ detail: 'No se pudo limpiar el historial.' }, { status: 502 });
	}
};
