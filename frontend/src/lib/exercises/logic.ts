import type {
	Answer,
	AuditChecklistAnswer,
	CompetenceMatrixAnswer,
	DocumentFormAnswer,
	Exercise,
	NonconformityFormAnswer,
	RiskTableAnswer,
	SoaDecision,
	TreatmentTableAnswer
} from './types';

/** Nivel de riesgo en escala UNSA (C + P en [0..4]) frente al umbral de aceptacion. */
export function computeRiskStatus(
	consequence: number | null,
	probability: number | null,
	threshold: number
): { level: number; acceptable: boolean } | null {
	if (consequence === null || probability === null) return null;
	const level = consequence + probability;
	return { level, acceptable: level < threshold };
}

/** Respuesta inicial de cada tipo de ejercicio (el orden mostrado es el orden barajado del API). */
export function initialAnswer(exercise: Exercise): Answer {
	switch (exercise.kind) {
		case 'soa_form':
			return { decisions: {} };
		case 'ordering':
			return { order: exercise.spec.items.map((item) => item.id) };
		case 'matching':
			return { assignments: {} };
		case 'single_choice':
			return { choice: '' };
		case 'quiz':
			return { answers: {} };
		case 'branching':
			return { choices: {} };
		case 'document_form': {
			const fields: Record<string, string | string[]> = {};
			for (const sec of exercise.spec.sections) {
				for (const field of sec.fields) {
					fields[field.id] = field.type === 'multiselect' ? [] : '';
				}
			}
			return { fields };
		}
		case 'risk_table': {
			const rows: RiskTableAnswer['rows'] = {};
			for (const row of exercise.spec.rows) {
				rows[row.id] = {
					consequence: null,
					probability: null,
					...(row.threat_options ? { threat: '' } : {}),
					...(row.vulnerability_options ? { vulnerability: '' } : {}),
					...(row.risk_owner_options ? { risk_owner: '' } : {})
				};
			}
			return { rows };
		}
		case 'treatment_table': {
			const rows: TreatmentTableAnswer['rows'] = {};
			for (const row of exercise.spec.rows) {
				rows[row.id] = {
					option: '',
					control_id: '',
					owner: '',
					deadline: '',
					residual_consequence: null,
					residual_probability: null
				};
			}
			return { rows };
		}
		case 'audit_checklist': {
			const items: AuditChecklistAnswer['items'] = {};
			for (const item of exercise.spec.items) {
				items[item.id] = { question_id: '', evidence_id: '', verdict: '' };
			}
			return { items };
		}
		case 'nonconformity_form': {
			const cases: NonconformityFormAnswer['cases'] = {};
			for (const c of exercise.spec.cases) {
				cases[c.id] = {
					correction: '',
					root_cause: '',
					requires_action: null,
					action: '',
					responsible: '',
					implementation_date: '',
					verification_date: '',
					verification: '',
					doc_change: null,
					affected_document: ''
				};
			}
			return { cases };
		}
		case 'competence_matrix': {
			const rows: CompetenceMatrixAnswer['rows'] = {};
			const withEval = Boolean(exercise.spec.evaluators);
			for (const row of exercise.spec.rows) {
				rows[row.id] = {
					competency_id: '',
					training_id: '',
					evidence_id: '',
					...(withEval ? { evaluator_id: '' } : {})
				};
			}
			return { rows };
		}
	}
}

/** Mueve el elemento `index` una posicion (delta = -1 sube, +1 baja). No muta el arreglo original. */
export function moveItem<T>(items: readonly T[], index: number, delta: -1 | 1): T[] {
	const target = index + delta;
	if (index < 0 || index >= items.length || target < 0 || target >= items.length) {
		return [...items];
	}
	const next = [...items];
	[next[index], next[target]] = [next[target], next[index]];
	return next;
}

/** Cuantos elementos hay que responder y cuantos ya lo estan (para habilitar el envio). */
export function completion(exercise: Exercise, answer: Answer): { done: number; total: number } {
	const count = (record: Record<string, string>) =>
		Object.values(record).filter((value) => value !== '').length;
	switch (exercise.kind) {
		case 'soa_form': {
			const decisions = (answer as { decisions: Record<string, SoaDecision> }).decisions;
			return {
				done: exercise.spec.controls.filter((control) => {
					const decision = decisions[control.id];
					return decision && decision.applies !== null && decision.reason !== '';
				}).length,
				total: exercise.spec.controls.length
			};
		}
		case 'ordering':
			return { done: exercise.spec.items.length, total: exercise.spec.items.length };
		case 'matching':
			return {
				done: count((answer as { assignments: Record<string, string> }).assignments),
				total: exercise.spec.left.length
			};
		case 'single_choice':
			return { done: (answer as { choice: string }).choice ? 1 : 0, total: 1 };
		case 'quiz':
			return {
				done: count((answer as { answers: Record<string, string> }).answers),
				total: exercise.spec.questions.length
			};
		case 'branching':
			return {
				done: count((answer as { choices: Record<string, string> }).choices),
				total: exercise.spec.steps.length
			};
		case 'document_form': {
			const fields = (answer as DocumentFormAnswer).fields;
			const requiredFields = exercise.spec.sections
				.flatMap((s) => s.fields)
				.filter((f) => f.required);
			const done = requiredFields.filter((f) => {
				const v = fields[f.id];
				return f.type === 'multiselect'
					? Array.isArray(v) && v.length > 0
					: typeof v === 'string' && v.trim() !== '';
			}).length;
			return { done, total: requiredFields.length };
		}
		case 'risk_table': {
			const rows = (answer as RiskTableAnswer).rows;
			const done = exercise.spec.rows.filter((r) => {
				const a = rows[r.id];
				if (!a || a.consequence === null || a.probability === null) return false;
				if (r.threat_options && !a.threat) return false;
				if (r.vulnerability_options && !a.vulnerability) return false;
				if (r.risk_owner_options && !a.risk_owner) return false;
				return true;
			}).length;
			return { done, total: exercise.spec.rows.length };
		}
		case 'treatment_table': {
			const rows = (answer as TreatmentTableAnswer).rows;
			const done = exercise.spec.rows.filter((r) => {
				const a = rows[r.id];
				if (!a || !a.option || !a.owner || !a.deadline) return false;
				if (a.option === 'controls' && !a.control_id) return false;
				return a.residual_consequence !== null && a.residual_probability !== null;
			}).length;
			return { done, total: exercise.spec.rows.length };
		}
		case 'audit_checklist': {
			const items = (answer as AuditChecklistAnswer).items;
			const done = exercise.spec.items.filter((it) => {
				const a = items[it.id];
				return Boolean(a && a.question_id && a.evidence_id && a.verdict);
			}).length;
			return { done, total: exercise.spec.items.length };
		}
		case 'nonconformity_form': {
			const cases = (answer as NonconformityFormAnswer).cases;
			const done = exercise.spec.cases.filter((c) => {
				const a = cases[c.id];
				if (!a) return false;
				if (
					!a.correction ||
					!a.root_cause ||
					a.requires_action === null ||
					!a.action ||
					!a.responsible ||
					!a.implementation_date ||
					!a.verification_date ||
					!a.verification ||
					a.doc_change === null
				) {
					return false;
				}
				return !a.doc_change || Boolean(a.affected_document);
			}).length;
			return { done, total: exercise.spec.cases.length };
		}
		case 'competence_matrix': {
			const rows = (answer as CompetenceMatrixAnswer).rows;
			const hasEval = Boolean(exercise.spec.evaluators);
			const done = exercise.spec.rows.filter((r) => {
				const a = rows[r.id];
				if (!a || !a.competency_id || !a.training_id || !a.evidence_id) return false;
				return !hasEval || Boolean(a.evaluator_id);
			}).length;
			return { done, total: exercise.spec.rows.length };
		}
	}
}

export function canSubmit(exercise: Exercise, answer: Answer): boolean {
	const { done, total } = completion(exercise, answer);
	return done === total;
}
