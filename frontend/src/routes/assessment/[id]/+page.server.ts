import { API_URL } from '$app/env/private';
import { error, fail, redirect } from '@sveltejs/kit';
import { apiGet, apiPost, errorMessage, type AssessmentAttempt } from '../../../lib/api';
import type { Actions, PageServerLoad } from './$types';

export const load: PageServerLoad = async ({ fetch, locals, params }) => {
	if (!locals.user) redirect(303, '/login');
	const { status, data } = await apiGet<AssessmentAttempt>(
		fetch,
		API_URL,
		`/assessments/${encodeURIComponent(params.id)}`,
		locals.token
	);
	if (!data) error(status === 404 || status === 422 ? 404 : 502, 'No se pudo cargar la evaluación');
	return { attempt: data };
};

export const actions: Actions = {
	default: async ({ request, fetch, locals, params }) => {
		if (!locals.user) redirect(303, '/login');
		let answers: unknown;
		try {
			answers = JSON.parse(String((await request.formData()).get('answers') ?? ''));
		} catch {
			return fail(400, { error: 'Las respuestas no son válidas.' });
		}
		const result = await apiPost(
			fetch,
			API_URL,
			`/assessments/${encodeURIComponent(params.id)}/submit`,
			locals.token,
			{ answers }
		);
		if (!result.data) {
			return fail(result.status || 503, {
				error: errorMessage(result.error, 'No se pudo enviar la evaluación.')
			});
		}
		redirect(303, `/assessment/${params.id}`);
	}
};
