import { API_URL } from '$app/env/private';
import { json, type RequestEvent } from '@sveltejs/kit';

type HttpMethod = 'GET' | 'POST' | 'DELETE' | 'PATCH';

/** Reenvia peticiones autenticadas del superadministrador hacia `/assistant/admin/*`. */
export async function proxyAdminAssistant(
	event: Pick<RequestEvent, 'fetch' | 'locals'>,
	backendPath: string,
	method: HttpMethod,
	body?: unknown
): Promise<Response> {
	if (!event.locals.user || !event.locals.token) {
		return json({ detail: 'No autenticado' }, { status: 401 });
	}
	if (event.locals.user.role !== 'superadmin') {
		return json({ detail: 'Permiso insuficiente' }, { status: 403 });
	}

	try {
		const response = await event.fetch(`${API_URL}${backendPath}`, {
			method,
			headers: {
				...(body !== undefined ? { 'Content-Type': 'application/json' } : {}),
				Authorization: `Bearer ${event.locals.token}`
			},
			body: body === undefined ? undefined : JSON.stringify(body)
		});
		const parsed = await response.json().catch(() => null);
		return json(parsed ?? { detail: 'Respuesta inválida del servidor' }, {
			status: response.status
		});
	} catch {
		return json(
			{ detail: 'No se pudo contactar al asistente administrador en este momento.' },
			{ status: 502 }
		);
	}
}
