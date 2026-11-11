import type { Exercise } from './exercises/types';

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

export type RouteStatus = 'locked' | 'available' | 'in_progress' | 'completed';
export type ModuleStatus = 'locked' | 'available' | 'completed';

export type RouteSummary = {
	code: string;
	order: number;
	title: string;
	description: string;
	hours: number;
	prerequisite_code: string | null;
	status: RouteStatus;
	modules_total: number;
	modules_completed: number;
	minutes_credited: number;
	hours_credited: number;
};
export type RoutesResponse = { routes: RouteSummary[]; total_hours_credited: number };

export type ModuleSummary = {
	id: string;
	order: number;
	title: string;
	minutes: number;
	mandatory: boolean;
	is_final: boolean;
	has_exercise: boolean;
	status: ModuleStatus;
	best_score: number | null;
};
export type RouteDetail = { route: RouteSummary; modules: ModuleSummary[] };

export type ModuleDetail = {
	id: string;
	route_code: string;
	title: string;
	minutes: number;
	is_final: boolean;
	status: ModuleStatus;
	best_score: number | null;
	lesson_md: string;
	exercise: Exercise | null;
};

export const ROUTE_STATUS_LABEL: Record<RouteStatus, string> = {
	locked: 'Bloqueada',
	available: 'Disponible',
	in_progress: 'En curso',
	completed: 'Aprobada'
};

export type LoginResult = {
	access_token: string;
	token_type: string;
	user: SessionUser;
};

export type DocumentSummary = {
	code: string;
	kind: string;
	title: string;
	owner_unit_code: string | null;
	owner_unit_name: string | null;
	lifecycle: 'in_force' | 'draft';
	review_date: string | null;
	current_version: number;
	updated_at: string;
	open_change_requests: number;
};
export type DocumentDetail = DocumentSummary & {
	content_md: string;
	content_hash: string;
	author_label: string;
	message: string;
};
export type VersionInfo = {
	number: number;
	message: string;
	author_label: string;
	created_at: string;
	content_hash: string;
	parent_number: number | null;
};

export type DiffLine = {
	kind: 'add' | 'del' | 'ctx';
	old_line: number | null;
	new_line: number | null;
	text: string;
};
export type Hunk = { old_start: number; new_start: number; lines: DiffLine[] };
export type DiffResult = { additions: number; deletions: number; hunks: Hunk[] };
export type VersionDiff = DiffResult & {
	document_code: string;
	from_version: number;
	to_version: number;
};

export type ChangeImpact = 'cosmetico' | 'procedimental' | 'estructural';
export type ChangeStatus = 'open' | 'approved' | 'rejected';
export type ChangeRequest = {
	id: string;
	document_code: string;
	title: string;
	rationale: string;
	impact: ChangeImpact;
	status: ChangeStatus;
	base_version: number;
	proposed_by_name: string;
	created_at: string;
	resolved_by_name: string | null;
	resolution_note: string | null;
	resulting_version: number | null;
	resolved_at: string | null;
};
export type ChangeRequestDetail = ChangeRequest & {
	proposed_content_md: string;
	diff: DiffResult;
};

export const IMPACT_LABEL: Record<ChangeImpact, string> = {
	cosmetico: 'Cosmético',
	procedimental: 'Procedimental',
	estructural: 'Estructural'
};
export const IMPACT_HINT: Record<ChangeImpact, string> = {
	cosmetico: 'solo cambia la redacción',
	procedimental: 'cambia cómo o cuándo se hace algo',
	estructural: 'cambia quién decide o responde'
};
export const CHANGE_STATUS_LABEL: Record<ChangeStatus, string> = {
	open: 'Abierta',
	approved: 'Aprobada',
	rejected: 'Rechazada'
};
export const DOCUMENT_KIND_LABEL: Record<string, string> = {
	ROF: 'ROF',
	MOF: 'MOF',
	ESTATUTO: 'Estatuto',
	CUADRO_ASIGNACION: 'Cuadro de asignación',
	REGLAMENTO: 'Reglamento',
	PIMS_SCOPE: 'PIMS · Alcance',
	PIMS_PRIVACY_POLICY: 'PIMS · Política',
	PIMS_RISK_PROCESS: 'PIMS · Proceso de riesgos',
	PIMS_SOA: 'PIMS · Aplicabilidad',
	PIMS_TREATMENT_PLAN: 'PIMS · Plan de tratamiento',
	PIMS_SECURITY_PROGRAM: 'PIMS · Programa de seguridad',
	PIMS_RISK_RESULTS: 'PIMS · Resultados de riesgos',
	PIMS_TREATMENT_RESULTS: 'PIMS · Resultados del tratamiento',
	PIMS_COMPETENCE: 'PIMS · Competencia',
	PIMS_MONITORING: 'PIMS · Monitoreo',
	PIMS_NONCONFORMITIES: 'PIMS · No conformidades'
};

export const LIFECYCLE_LABEL: Record<string, string> = {
	in_force: 'Vigente',
	draft: 'Borrador'
};

export type RequirementState = 'in_force' | 'draft' | 'expired' | 'unowned' | 'missing';
export const REQUIREMENT_STATE_LABEL: Record<RequirementState, string> = {
	in_force: 'Vigente',
	draft: 'Borrador',
	expired: 'Vencido',
	unowned: 'Sin responsable',
	missing: 'No existe'
};

export type PimsRequirement = {
	code: string;
	order: number;
	clause_ref: string;
	title: string;
	document_kind: string;
	summary: string;
	expected_evidence: string;
	responsible_unit_code: string | null;
	responsible_unit_name: string | null;
};
export type PimsDocument = {
	code: string;
	title: string;
	current_version: number;
	lifecycle: 'in_force' | 'draft';
	review_date: string | null;
	owner_unit_code: string | null;
	owner_unit_name: string | null;
};
export type PimsItem = PimsRequirement & {
	state: RequirementState;
	issues: RequirementState[];
	document: PimsDocument | null;
};
export type PimsCompleteness = {
	as_of: string;
	total: number;
	in_force: number;
	percent_in_force: number;
	counts: Record<RequirementState, number>;
	items: PimsItem[];
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

/** POST autenticado con cuerpo JSON. Devuelve status y el cuerpo ya parseado (o null). */
export async function apiPost<T>(
	fetchFn: FetchFn,
	baseUrl: string,
	path: string,
	token: string | null,
	body?: unknown
): Promise<{ status: number; data: T | null; error: unknown }> {
	try {
		const response = await fetchFn(`${baseUrl}${path}`, {
			method: 'POST',
			headers: {
				'Content-Type': 'application/json',
				...(token ? { Authorization: `Bearer ${token}` } : {})
			},
			body: body === undefined ? undefined : JSON.stringify(body)
		});
		const parsed = await response.json().catch(() => null);
		return response.ok
			? { status: response.status, data: parsed as T, error: null }
			: { status: response.status, data: null, error: parsed };
	} catch {
		return { status: 0, data: null, error: null };
	}
}

/** Traduce un error de FastAPI (`detail` string, objeto con `message` o lista de validacion). */
export function errorMessage(body: unknown, fallback: string): string {
	const detail = (body as { detail?: unknown } | null)?.detail;
	if (typeof detail === 'string') return detail;
	if (detail && typeof detail === 'object' && !Array.isArray(detail)) {
		const message = (detail as { message?: unknown }).message;
		if (typeof message === 'string') return message;
	}
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
