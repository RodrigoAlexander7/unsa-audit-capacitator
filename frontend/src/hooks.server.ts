import { API_URL } from '$app/env/private';
import type { Handle } from '@sveltejs/kit/hooks';
import { apiGet, type SessionUser } from './lib/api';
import { TOKEN_COOKIE } from './lib/session';

/** Resuelve el usuario de la sesion a partir de la cookie httpOnly con el JWT. */
export const handle: Handle = async ({ event, resolve }) => {
	const token = event.cookies.get(TOKEN_COOKIE) ?? null;
	event.locals.token = token;
	event.locals.user = null;

	if (token) {
		const { status, data } = await apiGet<SessionUser>(event.fetch, API_URL, '/me', token);
		if (data) event.locals.user = data;
		else if (status === 401) event.cookies.delete(TOKEN_COOKIE, { path: '/' });
	}
	return resolve(event);
};
