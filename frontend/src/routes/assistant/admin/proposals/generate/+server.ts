import { proxyAdminAssistant } from '../../../../../lib/server/adminAssistantProxy';
import type { RequestHandler } from './$types';

export const POST: RequestHandler = async (event) => {
	const body = await event.request.json().catch(() => ({}));
	return proxyAdminAssistant(event, '/assistant/admin/proposals/generate', 'POST', body);
};
