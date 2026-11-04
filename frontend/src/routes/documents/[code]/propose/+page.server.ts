import { API_URL } from '$app/env/private';
import { error, fail, redirect } from '@sveltejs/kit';
import {
	apiGet,
	apiPost,
	errorMessage,
	type ChangeRequest,
	type DocumentDetail
} from '../../../../lib/api';
import type { Actions, PageServerLoad } from './$types';

export const load: PageServerLoad = async ({ fetch, locals, params }) => {
	if (!locals.user) redirect(303, '/login');
	const { status, data } = await apiGet<DocumentDetail>(
		fetch,
		API_URL,
		`/documents/${encodeURIComponent(params.code)}`,
		locals.token
	);
	if (!data) error(status === 404 ? 404 : 502, 'No se pudo cargar el documento');
	return { doc: data };
};

export const actions: Actions = {
	default: async ({ request, fetch, locals, params }) => {
		if (!locals.user) redirect(303, '/login');
		const form = await request.formData();
		const values = {
			title: String(form.get('title') ?? ''),
			rationale: String(form.get('rationale') ?? ''),
			impact: String(form.get('impact') ?? ''),
			proposed_content_md: String(form.get('proposed_content_md') ?? '')
		};

		const result = await apiPost<ChangeRequest>(
			fetch,
			API_URL,
			`/documents/${encodeURIComponent(params.code)}/change-requests`,
			locals.token,
			values
		);
		if (!result.data) {
			return fail(result.status || 503, {
				values,
				error: errorMessage(result.error, 'No se pudo enviar la solicitud.')
			});
		}
		redirect(303, `/documents/${params.code}/changes/${result.data.id}`);
	}
};
