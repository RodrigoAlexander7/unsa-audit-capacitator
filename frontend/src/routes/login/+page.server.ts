import { API_URL } from '$app/env/private';
import { fail, redirect } from '@sveltejs/kit';
import { errorMessage, type LoginResult } from '../../lib/api';
import { TOKEN_COOKIE, TOKEN_MAX_AGE_SECONDS } from '../../lib/session';
import type { Actions, PageServerLoad } from './$types';

export const load: PageServerLoad = ({ locals }) => {
	if (locals.user) redirect(303, '/');
};

export const actions: Actions = {
	default: async ({ request, fetch, cookies, url }) => {
		const form = await request.formData();
		const email = String(form.get('email') ?? '').trim();
		const password = String(form.get('password') ?? '');

		const response = await fetch(`${API_URL}/auth/login`, {
			method: 'POST',
			headers: { 'Content-Type': 'application/json' },
			body: JSON.stringify({ email, password })
		}).catch(() => null);

		if (!response)
			return fail(503, {
				email,
				error: 'No se pudo contactar con el servidor.'
			});
		if (!response.ok) {
			return fail(response.status, {
				email,
				error: errorMessage(await response.json().catch(() => null), 'No se pudo iniciar sesión.')
			});
		}

		const result = (await response.json()) as LoginResult;
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
