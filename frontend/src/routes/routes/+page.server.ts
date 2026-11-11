import { API_URL } from '$app/env/private';
import { redirect } from '@sveltejs/kit';
import { apiGet, type RoutesResponse } from '../../lib/api';
import type { PageServerLoad } from './$types';

export const load: PageServerLoad = async ({ fetch, locals }) => {
	if (!locals.user) redirect(303, '/login');
	const { data } = await apiGet<RoutesResponse>(fetch, API_URL, '/routes', locals.token);
	return { listing: data };
};
