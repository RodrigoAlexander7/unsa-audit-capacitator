import { API_URL } from '$app/env/private';
import { fetchHealth } from '../lib/health';
import type { PageServerLoad } from './$types';

export const load: PageServerLoad = async ({ fetch }) => {
	return { status: await fetchHealth(fetch, API_URL) };
};
