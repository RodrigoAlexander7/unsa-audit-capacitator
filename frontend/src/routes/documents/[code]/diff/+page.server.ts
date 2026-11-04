import { API_URL } from '$app/env/private';
import { error, redirect } from '@sveltejs/kit';
import { apiGet, type VersionDiff, type VersionInfo } from '../../../../lib/api';
import type { PageServerLoad } from './$types';

export const load: PageServerLoad = async ({ fetch, locals, params, url }) => {
	if (!locals.user) redirect(303, '/login');
	const code = encodeURIComponent(params.code);
	const versions = await apiGet<VersionInfo[]>(
		fetch,
		API_URL,
		`/documents/${code}/versions`,
		locals.token
	);
	if (!versions.data) error(versions.status === 404 ? 404 : 502, 'No se pudo cargar el documento');

	const numbers = versions.data.map((v) => v.number);
	const latest = Math.max(...numbers);
	const to = Number(url.searchParams.get('to')) || latest;
	const from = Number(url.searchParams.get('from')) || Math.max(1, to - 1);

	const diff = await apiGet<VersionDiff>(
		fetch,
		API_URL,
		`/documents/${code}/diff?from=${from}&to=${to}`,
		locals.token
	);
	return {
		code: params.code,
		versions: versions.data,
		from,
		to,
		diff: diff.data,
		notFound: diff.status === 404
	};
};
