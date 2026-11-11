import { API_URL } from '$app/env/private';
import { requireSuperadmin } from '../../lib/admin';
import {
	apiGet,
	type AssessmentProfileStats,
	type PimsCompleteness,
	type RouteDetailStats,
	type RouteStats
} from '../../lib/api';
import type { PageServerLoad } from './$types';

export const load: PageServerLoad = async ({ fetch, locals }) => {
	requireSuperadmin(locals);
	const get = <T>(path: string) => apiGet<T>(fetch, API_URL, path, locals.token);

	const [routes, assessments, pims] = await Promise.all([
		get<RouteStats[]>('/admin/stats/routes'),
		get<AssessmentProfileStats[]>('/admin/stats/assessments'),
		get<PimsCompleteness>('/pims/completeness')
	]);

	const details = await Promise.all(
		(routes.data ?? []).map((route) => get<RouteDetailStats>(`/admin/stats/routes/${route.code}`))
	);
	const hardest = details
		.flatMap((detail) =>
			(detail.data?.modules ?? [])
				.filter((module) => module.hardest)
				.map((module) => ({ ...module, route_title: detail.data?.route.title ?? '' }))
		)
		.sort((a, b) => (a.pass_rate ?? 0) - (b.pass_rate ?? 0));

	return {
		routes: routes.data,
		assessments: assessments.data ?? [],
		pims: pims.data,
		hardest
	};
};
