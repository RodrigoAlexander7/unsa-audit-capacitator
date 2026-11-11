import { API_URL } from '$app/env/private';
import { fail, redirect } from '@sveltejs/kit';
import { errorMessage, type LoginResult } from '../../lib/api';
import { TOKEN_COOKIE, TOKEN_MAX_AGE_SECONDS } from '../../lib/session';
import type { Actions, PageServerLoad } from './$types';

export const load: PageServerLoad = ({ locals }) => {
	if (locals.user) redirect(303, '/');
};

async function post(fetchFn: typeof fetch, path: string, body: unknown) {
	return fetchFn(`${API_URL}${path}`, {
		method: 'POST',
		headers: { 'Content-Type': 'application/json' },
		body: JSON.stringify(body)
	}).catch(() => null);
}

export const actions: Actions = {
	default: async ({ request, fetch, cookies, url }) => {
		const form = await request.formData();
		const full_name = String(form.get('full_name') ?? '').trim();
		const email = String(form.get('email') ?? '').trim();
		const password = String(form.get('password') ?? '');

		const created = await post(fetch, '/auth/register', {
			email,
			password,
			full_name
		});
		if (!created)
			return fail(503, {
				email,
				full_name,
				error: 'No se pudo contactar con el servidor.'
			});
		if (!created.ok) {
			return fail(created.status, {
				email,
				full_name,
				error: errorMessage(
					await created.json().catch(() => null),
					'No se pudo completar el registro.'
				)
			});
		}

		// Inicia sesion automaticamente tras registrarse.
		const login = await post(fetch, '/auth/login', { email, password });
		if (!login?.ok) redirect(303, '/login');
		const result = (await login.json()) as LoginResult;
		cookies.set(TOKEN_COOKIE, result.access_token, {
			path: '/',
			httpOnly: true,
			sameSite: 'lax',
			secure: url.protocol === 'https:',
			maxAge: TOKEN_MAX_AGE_SECONDS
		});
		redirect(303, '/');
	}
};
