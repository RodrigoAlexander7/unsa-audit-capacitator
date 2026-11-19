import { API_URL } from '$app/env/private';
import { error, fail, redirect } from '@sveltejs/kit';
import { renderMarkdown } from '../../../../lib/markdown';
import {
	apiGet,
	apiPost,
	errorMessage,
	type ModuleDetail,
	type RouteDetail
} from '../../../../lib/api';
import type { AttemptResult } from '../../../../lib/exercises/types';
import type { Actions, PageServerLoad } from './$types';

export const load: PageServerLoad = async ({ fetch, locals, params }) => {
	if (!locals.user) redirect(303, '/login');
	const id = encodeURIComponent(params.module);
	const { status, data } = await apiGet<ModuleDetail>(
		fetch,
		API_URL,
		`/modules/${id}`,
		locals.token
	);
	if (!data) {
		if (status === 403 || status === 409) redirect(303, `/routes/${params.code}`);
		error(status === 404 || status === 422 ? 404 : 502, 'No se pudo cargar el módulo');
	}

	const route = await apiGet<RouteDetail>(
		fetch,
		API_URL,
		`/routes/${encodeURIComponent(data.route_code)}`,
		locals.token
	);
	const current = route.data?.modules.find((m) => m.id === data.id);
	const next = route.data?.modules.find(
		(m) => current && m.order > current.order && m.status !== 'locked'
	);

	const lessonHtml = renderMarkdown(data.lesson_md);
	const referenceHtml = data.reference ? renderMarkdown(data.reference.body_md) : null;
	return {
		module: data,
		lessonHtml,
		referenceHtml,
		routeTitle: route.data?.route.title ?? '',
		nextModuleId: next?.id ?? null
	};
};

export const actions: Actions = {
	default: async ({ request, fetch, locals, params }) => {
		if (!locals.user) redirect(303, '/login');
		const form = await request.formData();
		let answer: unknown;
		try {
			answer = JSON.parse(String(form.get('answer') ?? ''));
		} catch {
			return fail(400, { error: 'La respuesta no es válida.' });
		}
		const result = await apiPost<AttemptResult>(
			fetch,
			API_URL,
			`/modules/${encodeURIComponent(params.module)}/attempts`,
			locals.token,
			{ answer }
		);
		if (!result.data) {
			return fail(result.status || 503, {
				error: errorMessage(result.error, 'No se pudo enviar la respuesta.')
			});
		}
		return { result: result.data };
	}
};
