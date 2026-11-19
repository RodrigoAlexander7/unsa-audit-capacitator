export type AssistantMessage = {
	id: string;
	question: string;
	status: 'ok' | 'refused' | 'error';
	answer: string | null;
	error: string | null;
	module_id: string | null;
	route_path: string | null;
	context_hash: string;
	duration_ms: number;
	created_at: string;
};

export type AssistantContextHint = {
	moduleId: string | null;
	routePath: string;
	label: string;
	suggestions: string[];
};

/** Deriva el contexto de la pagina actual sin incluir PII ni claves de ejercicios. */
export function detectAssistantContext(
	pathname: string,
	params: Record<string, string | undefined>
): AssistantContextHint {
	if (params.module && pathname.startsWith('/routes/')) {
		return {
			moduleId: params.module,
			routePath: pathname,
			label: 'Contexto: módulo actual y UNSA',
			suggestions: [
				'¿Cómo se aplica este tema en la UNSA ficticia?',
				'¿Qué criterio normativo sustenta esta lección?',
				'¿Qué sistemas o documentos del PIMS se relacionan con este módulo?'
			]
		};
	}

	if (pathname.startsWith('/documents')) {
		return {
			moduleId: null,
			routePath: pathname,
			label: 'Contexto: documentos del PIMS',
			suggestions: [
				'¿Qué unidad orgánica responde por los documentos del PIMS?',
				'¿Por qué importa distinguir borrador, vencido y vigente al auditar?'
			]
		};
	}

	return {
		moduleId: null,
		routePath: pathname || '/',
		label: 'Contexto: UNSA ficticia y PIMS',
		suggestions: [
			'¿Qué sistemas de la UNSA tratan datos personales?',
			'¿Cuál es la diferencia entre responsable y encargado según ISO/IEC 27701?',
			'¿Qué documentos del PIMS requieren actualización en la UNSA?'
		]
	};
}

export type CohortAliasItem = {
	alias: string;
	full_name: string;
	email: string;
	stalled: boolean;
	overall_progress_pct: number;
};

export type CohortSummary = {
	total_learners: number;
	stalled_count: number;
	aliases: CohortAliasItem[];
};

export type AdminAskResponse = {
	message: AssistantMessage;
	aliases: CohortAliasItem[];
};

export type ProposalStatus = 'draft' | 'accepted' | 'discarded';

export type CurriculumProposal = {
	id: string;
	title: string;
	target_route_code: string | null;
	target_module_slug: string | null;
	change_type: string;
	proposed_change: string;
	rationale: string;
	evidence_metrics: Record<string, unknown>;
	status: ProposalStatus;
	review_note: string | null;
	created_at: string;
	reviewed_at: string | null;
};

export type GenerateProposalsResponse = {
	summary: string;
	proposals: CurriculumProposal[];
};

/** Resuelve localmente alias P-xx -> Nombre (P-xx) sin exponer PII al modelo. */
export function resolveAliasesInText(text: string, aliases: CohortAliasItem[]): string {
	if (!text || aliases.length === 0) return text;
	const byAlias = new Map(aliases.map((item) => [item.alias, item]));
	return text.replace(/\b(P-\d{2,3})\b(?!\))/g, (match, code: string, offset: number) => {
		const entry = byAlias.get(code);
		if (!entry) return match;
		const before = text.slice(Math.max(0, offset - entry.full_name.length - 6), offset);
		if (before.includes(entry.full_name)) return match;
		return `**${entry.full_name}** (${code})`;
	});
}
