import { API_URL } from '$app/env/private';
import { error, fail, redirect } from '@sveltejs/kit';
import { apiGet, apiPost, errorMessage, type ChangeRequestDetail } from '../../../../../lib/api';
import type { Actions, PageServerLoad } from './$types';

export const load: PageServerLoad = async ({ fetch, locals, params }) => {
	if (!locals.user) redirect(303, '/login');
	const { status, data } = await apiGet<ChangeRequestDetail>(
		fetch,
		API_URL,
		`/change-requests/${encodeURIComponent(params.id)}`,
		locals.token
	);
	if (!data) error(status === 404 || status === 422 ? 404 : 502, 'No se pudo cargar la solicitud');
	return { change: data };
};

async function resolve(
	decision: 'approve' | 'reject',
	{
		request,
		fetch,
		locals,
		params
	}: {
		request: Request;
		fetch: typeof globalThis.fetch;
		locals: App.Locals;
		params: { code: string; id: string };
	}
) {
	if (!locals.user) redirect(303, '/login');
	const form = await request.formData();
	const note = String(form.get('note') ?? '');
	const result = await apiPost(
		fetch,
		API_URL,
		`/change-requests/${encodeURIComponent(params.id)}/resolve`,
		locals.token,
		{ decision, note }
	);
	if (!result.data) {
		return fail(result.status || 503, {
			note,
			error: errorMessage(result.error, 'No se pudo resolver la solicitud.')
		});
	}
	redirect(303, `/documents/${params.code}/changes/${params.id}`);
}

export const actions: Actions = {
	approve: (event) => resolve('approve', event),
	reject: (event) => resolve('reject', event)
};
