import { API_URL } from '$app/env/private';
import { redirect } from '@sveltejs/kit';
import { apiGet, type PimsCompleteness } from '../../../lib/api';
import type { PageServerLoad } from './$types';

export const load: PageServerLoad = async ({ fetch, locals }) => {
	if (!locals.user) redirect(303, '/login');
	const { data } = await apiGet<PimsCompleteness>(
		fetch,
		API_URL,
		'/pims/completeness',
		locals.token
	);
	return { completeness: data };
};
