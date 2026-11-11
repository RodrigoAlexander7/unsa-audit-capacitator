import { API_URL } from '$app/env/private';
import { redirect } from '@sveltejs/kit';
import { apiGet, type ChangeRequest, type DocumentSummary } from '../../lib/api';
import type { PageServerLoad } from './$types';

export const load: PageServerLoad = async ({ fetch, locals }) => {
	if (!locals.user) redirect(303, '/login');
	const [documents, open] = await Promise.all([
		apiGet<DocumentSummary[]>(fetch, API_URL, '/documents', locals.token),
		apiGet<ChangeRequest[]>(fetch, API_URL, '/change-requests?status=open', locals.token)
	]);
	return { documents: documents.data ?? [], openRequests: open.data ?? [] };
};
