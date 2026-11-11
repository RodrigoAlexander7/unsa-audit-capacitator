import { API_URL } from '$app/env/private';
import { fail, redirect } from '@sveltejs/kit';
import {
	apiGet,
	apiPost,
	errorMessage,
	type AssessmentAttempt,
	type AssessmentSummary
} from '../../lib/api';
import type { Actions, PageServerLoad } from './$types';

export const load: PageServerLoad = async ({ fetch, locals }) => {
	if (!locals.user) redirect(303, '/login');
	const { data } = await apiGet<AssessmentSummary[]>(fetch, API_URL, '/assessments', locals.token);
	return { attempts: data ?? [] };
};

export const actions: Actions = {
	default: async ({ request, fetch, locals }) => {
		if (!locals.user) redirect(303, '/login');
		const profile = String((await request.formData()).get('profile') ?? '');
		const result = await apiPost<AssessmentAttempt>(fetch, API_URL, '/assessments', locals.token, {
			profile
		});
		if (!result.data) {
			return fail(result.status || 503, {
				error: errorMessage(result.error, 'No se pudo iniciar la evaluación.')
			});
		}
		redirect(303, `/assessment/${result.data.id}`);
	}
};
