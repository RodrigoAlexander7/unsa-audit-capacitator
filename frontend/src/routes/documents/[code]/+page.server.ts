import { API_URL } from '$app/env/private';
import { error, redirect } from '@sveltejs/kit';
import { renderMarkdown } from '../../../lib/markdown';
import {
	apiGet,
	type ChangeRequest,
	type DocumentDetail,
	type VersionInfo
} from '../../../lib/api';
import type { PageServerLoad } from './$types';

export const load: PageServerLoad = async ({ fetch, locals, params }) => {
	if (!locals.user) redirect(303, '/login');
	const code = encodeURIComponent(params.code);
	const [doc, versions, requests] = await Promise.all([
		apiGet<DocumentDetail>(fetch, API_URL, `/documents/${code}`, locals.token),
		apiGet<VersionInfo[]>(fetch, API_URL, `/documents/${code}/versions`, locals.token),
		apiGet<ChangeRequest[]>(fetch, API_URL, `/documents/${code}/change-requests`, locals.token)
	]);
	if (!doc.data) error(doc.status === 404 ? 404 : 502, 'No se pudo cargar el documento');

	return {
		doc: doc.data,
		html: renderMarkdown(doc.data.content_md),
		versions: [...(versions.data ?? [])].reverse(),
		requests: requests.data ?? []
	};
};
