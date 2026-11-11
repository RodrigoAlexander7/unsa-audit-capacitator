import { API_URL } from '$app/env/private';
import { error, fail, redirect } from '@sveltejs/kit';
import { apiGet, apiPost, errorMessage, type RouteDetail } from '../../../lib/api';
import type { Actions, PageServerLoad } from './$types';

export const load: PageServerLoad = async ({ fetch, locals, params }) => {
	if (!locals.user) redirect(303, '/login');
	const { status, data } = await apiGet<RouteDetail>(
		fetch,
		API_URL,
		`/routes/${encodeURIComponent(params.code)}`,
		locals.token
	);
	if (!data) error(status === 404 ? 404 : 502, 'No se pudo cargar la ruta');
	return { detail: data };
};

export const actions: Actions = {
	enroll: async ({ fetch, locals, params }) => {
		if (!locals.user) redirect(303, '/login');
		const result = await apiPost(
			fetch,
			API_URL,
			`/routes/${encodeURIComponent(params.code)}/enroll`,
			locals.token
		);
		if (result.status !== 200 && result.status !== 201) {
			return fail(result.status || 503, {
				error: errorMessage(result.error, 'No se pudo completar la matrícula.')
			});
		}
		redirect(303, `/routes/${params.code}`);
	}
};
