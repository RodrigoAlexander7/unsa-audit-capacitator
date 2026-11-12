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
