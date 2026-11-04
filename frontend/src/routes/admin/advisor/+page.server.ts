import { API_URL } from '$app/env/private';
import { fail } from '@sveltejs/kit';
import { requireSuperadmin } from '../../../lib/admin';
import { apiGet, apiPost, errorMessage, type AdvisorQuery } from '../../../lib/api';
import type { Actions, PageServerLoad } from './$types';

export const load: PageServerLoad = async ({ fetch, locals }) => {
	requireSuperadmin(locals);
	const { data } = await apiGet<AdvisorQuery[]>(
		fetch,
		API_URL,
		'/admin/advisor/history',
		locals.token
	);
	return { history: data ?? [] };
};

export const actions: Actions = {
	default: async ({ request, fetch, locals }) => {
		requireSuperadmin(locals);
		const question = String((await request.formData()).get('question') ?? '').trim();
		if (!question) return fail(422, { question, error: 'Escribe una pregunta.' });
		if (question.length > 1000) {
			return fail(422, { question, error: 'La pregunta no puede superar los 1000 caracteres.' });
		}

		const result = await apiPost<AdvisorQuery>(fetch, API_URL, '/admin/advisor/ask', locals.token, {
			question
		});
		if (!result.data) {
			return fail(result.status || 503, {
				question,
				error: errorMessage(result.error, 'No se pudo consultar al asesor.')
			});
		}
		return { question, answer: result.data.answer ?? '' };
	}
};
