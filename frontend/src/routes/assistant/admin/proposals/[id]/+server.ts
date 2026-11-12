import { json } from '@sveltejs/kit';
import { proxyAdminAssistant } from '../../../../../lib/server/adminAssistantProxy';
import type { RequestHandler } from './$types';

export const PATCH: RequestHandler = async (event) => {
	const body = await event.request.json().catch(() => null);
	if (!body || typeof body !== 'object') {
		return json({ detail: 'Solicitud inválida' }, { status: 422 });
	}
	return proxyAdminAssistant(event, `/assistant/admin/proposals/${event.params.id}`, 'PATCH', body);
};
