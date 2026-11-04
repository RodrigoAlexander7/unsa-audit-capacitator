export type SessionUser = {
	id: string;
	email: string;
	full_name: string;
	role: 'learner' | 'superadmin';
};

export type OrgUnitSummary = {
	id: string;
	kind: string;
	name: string;
	code: string;
};
export type OrgTree = OrgUnitSummary & { children: OrgTree[] };

export type Person = { id: string; full_name: string; kind: string };
export type Position = {
	id: string;
	title: string;
	reports_to_title: string | null;
	holder: Person | null;
};
export type OrgUnitDetail = {
	unit: OrgUnitSummary;
	parent: OrgUnitSummary | null;
	children: OrgUnitSummary[];
	positions: Position[];
};

export type SystemInfo = {
	id: string;
	name: string;
	description: string;
	owner_unit: OrgUnitSummary;
	data_categories: string[];
	owners: { person: Person; role: string }[];
};

export type LoginResult = {
	access_token: string;
	token_type: string;
	user: SessionUser;
};

type FetchFn = typeof fetch;

/** GET autenticado contra el API. Devuelve null si el servidor responde con error. */
export async function apiGet<T>(
	fetchFn: FetchFn,
	baseUrl: string,
	path: string,
	token: string | null
): Promise<{ status: number; data: T | null }> {
	try {
		const response = await fetchFn(`${baseUrl}${path}`, {
			headers: token ? { Authorization: `Bearer ${token}` } : {}
		});
		if (!response.ok) return { status: response.status, data: null };
		return { status: response.status, data: (await response.json()) as T };
	} catch {
		return { status: 0, data: null };
	}
}

/** Traduce un error de FastAPI (`detail` string o lista de validacion) a un mensaje legible. */
export function errorMessage(body: unknown, fallback: string): string {
	const detail = (body as { detail?: unknown } | null)?.detail;
	if (typeof detail === 'string') return detail;
	if (Array.isArray(detail) && detail.length > 0) return 'Revisa los datos ingresados.';
	return fallback;
}

export const KIND_LABEL: Record<string, string> = {
	rectorado: 'Rectorado',
	vicerrectorado: 'Vicerrectorado',
	facultad: 'Facultad',
	escuela: 'Escuela',
	oficina: 'Oficina'
};

export const ROLE_LABEL: Record<string, string> = {
	controller: 'Responsable (controller)',
	processor: 'Encargado (processor)',
	steward: 'Custodio (steward)'
};
