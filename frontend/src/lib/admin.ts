import { redirect } from '@sveltejs/kit';

/** Solo el superadmin entra al panel; el resto vuelve al inicio (el backend igual responde 403). */
export function requireSuperadmin(locals: App.Locals): void {
	if (!locals.user) redirect(303, '/login');
	if (locals.user.role !== 'superadmin') redirect(303, '/');
}
