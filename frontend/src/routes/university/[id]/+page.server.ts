import { API_URL } from '$app/env/private';
import { error, redirect } from '@sveltejs/kit';
import { apiGet, type OrgUnitDetail } from '../../../lib/api';
import type { PageServerLoad } from './$types';

export const load: PageServerLoad = async ({ fetch, locals, params }) => {
	if (!locals.user) redirect(303, '/login');
	const { status, data } = await apiGet<OrgUnitDetail>(
		fetch,
		API_URL,
		`/org-units/${encodeURIComponent(params.id)}`,
		locals.token
	);
	if (!data) error(status === 404 || status === 422 ? 404 : 502, 'No se pudo cargar la unidad');
	return { detail: data };
};
