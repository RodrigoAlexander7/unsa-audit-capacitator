import { API_URL } from '$app/env/private';
import { json } from '@sveltejs/kit';
import type { RequestHandler } from './$types';

export const POST: RequestHandler = async ({ request, fetch, locals }) => {
	if (!locals.user || !locals.token) {
		return json({ detail: 'No autenticado' }, { status: 401 });
	}
	const body = await request.json().catch(() => null);
	if (!body || typeof body !== 'object') {
		return json({ detail: 'Solicitud inválida' }, { status: 422 });
	}

	try {
		const response = await fetch(`${API_URL}/assistant/ask`, {
			method: 'POST',
			headers: {
				'Content-Type': 'application/json',
				Authorization: `Bearer ${locals.token}`
			},
			body: JSON.stringify(body)
		});
		const parsed = await response.json().catch(() => null);
		return json(parsed ?? { detail: 'Respuesta inválida del servidor' }, {
			status: response.status
		});
	} catch {
		return json({ detail: 'No se pudo contactar al asistente en este momento.' }, { status: 502 });
	}
};
