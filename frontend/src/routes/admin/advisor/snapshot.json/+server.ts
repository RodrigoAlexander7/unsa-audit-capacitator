import { API_URL } from '$app/env/private';
import { error } from '@sveltejs/kit';
import { requireSuperadmin } from '../../../../lib/admin';
import type { RequestHandler } from './$types';

/** Descarga el snapshot anonimizado (el JWT es httpOnly, por eso pasa por el servidor). */
export const GET: RequestHandler = async ({ fetch, locals }) => {
	requireSuperadmin(locals);
	const response = await fetch(`${API_URL}/admin/advisor/snapshot`, {
		headers: { Authorization: `Bearer ${locals.token}` }
	});
	if (!response.ok) error(response.status, 'No se pudo generar el snapshot');
	const body = (await response.json()) as { data: unknown };
	return new Response(JSON.stringify(body.data, null, 2), {
		headers: {
			'Content-Type': 'application/json; charset=utf-8',
			'Content-Disposition': 'attachment; filename="snapshot-unsa-capacitacion.json"'
		}
	});
};
