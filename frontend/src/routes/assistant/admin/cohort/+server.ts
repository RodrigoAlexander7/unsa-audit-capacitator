import { proxyAdminAssistant } from '../../../../lib/server/adminAssistantProxy';
import type { RequestHandler } from './$types';

export const GET: RequestHandler = (event) =>
	proxyAdminAssistant(event, '/assistant/admin/cohort', 'GET');
