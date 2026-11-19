import { describe, expect, it } from 'vitest';
import { canSubmit, completion, computeRiskStatus, initialAnswer, moveItem } from './logic';
import type { Exercise } from './types';

const opts = (...ids: string[]) => ids.map((id) => ({ id, label: id.toUpperCase() }));

describe('moveItem', () => {
	it('sube y baja sin mutar el original', () => {
		const original = ['a', 'b', 'c'];
		expect(moveItem(original, 2, -1)).toEqual(['a', 'c', 'b']);
		expect(moveItem(original, 0, 1)).toEqual(['b', 'a', 'c']);
		expect(original).toEqual(['a', 'b', 'c']);
	});

	it('ignora movimientos fuera de rango', () => {
		expect(moveItem(['a', 'b'], 0, -1)).toEqual(['a', 'b']);
		expect(moveItem(['a', 'b'], 1, 1)).toEqual(['a', 'b']);
		expect(moveItem(['a', 'b'], 5, -1)).toEqual(['a', 'b']);
	});
});

describe('initialAnswer y completion', () => {
	const ordering: Exercise = {
		kind: 'ordering',
		pass_score: 70,
		spec: { prompt: 'p', items: opts('x', 'y', 'z') }
	};
	const matching: Exercise = {
		kind: 'matching',
		pass_score: 70,
		spec: { prompt: 'p', left: opts('l1', 'l2'), right: opts('r1') }
	};
	const quiz: Exercise = {
		kind: 'quiz',
		pass_score: 70,
		spec: {
			prompt: 'p',
			questions: [
				{ id: 'q1', prompt: 'a', options: opts('a', 'b') },
				{ id: 'q2', prompt: 'b', options: opts('a', 'b') }
			]
		}
	};
	const single: Exercise = {
		kind: 'single_choice',
		pass_score: 70,
		spec: { prompt: 'p', options: opts('a', 'b') }
	};
	const branching: Exercise = {
		kind: 'branching',
		pass_score: 70,
		spec: { prompt: 'p', steps: [{ id: 's1', situation: 'x', options: opts('a', 'b') }] }
	};

	it('ordering parte con el orden barajado recibido y siempre se puede enviar', () => {
		const answer = initialAnswer(ordering);
		expect(answer).toEqual({ order: ['x', 'y', 'z'] });
		expect(canSubmit(ordering, answer)).toBe(true);
	});

	it('soa_form exige decidir aplicabilidad y justificacion de cada control', () => {
		const soa: Exercise = {
			kind: 'soa_form',
			pass_score: 70,
			spec: {
				prompt: 'p',
				scenario: 's',
				reasons: opts('r1', 'r2'),
				controls: opts('c1', 'c2')
			}
		};
		expect(initialAnswer(soa)).toEqual({ decisions: {} });
		expect(completion(soa, { decisions: { c1: { applies: true, reason: 'r1' } } })).toEqual({
			done: 1,
			total: 2
		});
		// aplicabilidad sin justificacion o justificacion sin aplicabilidad no cuentan
		expect(
			canSubmit(soa, {
				decisions: { c1: { applies: true, reason: 'r1' }, c2: { applies: false, reason: '' } }
			})
		).toBe(false);
		expect(
			canSubmit(soa, {
				decisions: { c1: { applies: true, reason: 'r1' }, c2: { applies: null, reason: 'r2' } }
			})
		).toBe(false);
		expect(
			canSubmit(soa, {
				decisions: { c1: { applies: true, reason: 'r1' }, c2: { applies: false, reason: 'r2' } }
			})
		).toBe(true);
	});

	it('matching exige asignar todos los elementos', () => {
		expect(initialAnswer(matching)).toEqual({ assignments: {} });
		expect(completion(matching, { assignments: { l1: 'r1' } })).toEqual({ done: 1, total: 2 });
		expect(canSubmit(matching, { assignments: { l1: 'r1', l2: '' } })).toBe(false);
		expect(canSubmit(matching, { assignments: { l1: 'r1', l2: 'r1' } })).toBe(true);
	});

	it('quiz, single_choice y branching exigen responder todo', () => {
		expect(canSubmit(quiz, { answers: { q1: 'a' } })).toBe(false);
		expect(canSubmit(quiz, { answers: { q1: 'a', q2: 'b' } })).toBe(true);
		expect(canSubmit(single, { choice: '' })).toBe(false);
		expect(canSubmit(single, { choice: 'a' })).toBe(true);
		expect(canSubmit(branching, { choices: {} })).toBe(false);
		expect(canSubmit(branching, { choices: { s1: 'a' } })).toBe(true);
	});

	it('computeRiskStatus calcula C + P frente al umbral', () => {
		expect(computeRiskStatus(null, 1, 3)).toBeNull();
		expect(computeRiskStatus(1, 1, 3)).toEqual({ level: 2, acceptable: true });
		expect(computeRiskStatus(2, 1, 3)).toEqual({ level: 3, acceptable: false });
	});

	it('document_form solo exige campos obligatorios y verifica multiselect', () => {
		const docForm: Exercise = {
			kind: 'document_form',
			pass_score: 70,
			spec: {
				prompt: 'p',
				scenario: 's',
				document_title: 'Alcance',
				sections: [
					{
						id: 's1',
						title: 'Cabecera',
						fields: [
							{ id: 'f_txt', label: 'Texto', type: 'text', required: true },
							{
								id: 'f_ms',
								label: 'Sistemas',
								type: 'multiselect',
								required: true,
								options: opts('a')
							},
							{ id: 'f_opt', label: 'Notas', type: 'textarea', required: false }
						]
					}
				]
			}
		};
		const init = initialAnswer(docForm);
		expect(init).toEqual({ fields: { f_txt: '', f_ms: [], f_opt: '' } });
		expect(canSubmit(docForm, init)).toBe(false);
		expect(completion(docForm, { fields: { f_txt: 'ok', f_ms: [] } })).toEqual({
			done: 1,
			total: 2
		});
		expect(canSubmit(docForm, { fields: { f_txt: 'ok', f_ms: ['a'] } })).toBe(true);
	});

	it('risk_table exige C, P y catálogos opcionales de fila cuando existen', () => {
		const riskEx: Exercise = {
			kind: 'risk_table',
			pass_score: 70,
			spec: {
				prompt: 'p',
				scenario: 's',
				threshold: 3,
				rows: [
					{
						id: 'r1',
						asset: 'SIS',
						asset_owner: 'TI',
						data_categories: ['academico'],
						existing_controls: 'TLS',
						threat: '',
						vulnerability: 'Sin MFA',
						risk_owner: 'Rector',
						threat_options: opts('t1', 't2')
					}
				]
			}
		};
		const init = initialAnswer(riskEx);
		expect(init).toEqual({
			rows: { r1: { consequence: null, probability: null, threat: '' } }
		});
		expect(
			canSubmit(riskEx, { rows: { r1: { consequence: 2, probability: 1, threat: '' } } })
		).toBe(false);
		expect(
			canSubmit(riskEx, { rows: { r1: { consequence: 2, probability: 1, threat: 't1' } } })
		).toBe(true);
	});

	it('treatment_table solo exige control de SoA cuando la opcion es aplicar controles', () => {
		const trEx: Exercise = {
			kind: 'treatment_table',
			pass_score: 70,
			spec: {
				prompt: 'p',
				scenario: 's',
				options: opts('controls', 'accept'),
				soa_controls: opts('c1'),
				owners: opts('ti'),
				rows: [
					{
						id: 'r1',
						asset: 'SIS',
						threat: 'T',
						vulnerability: 'V',
						initial_consequence: 2,
						initial_probability: 2,
						initial_risk: 4,
						risk_owner: 'TI'
					}
				]
			}
		};
		expect(
			canSubmit(trEx, {
				rows: {
					r1: {
						option: 'controls',
						control_id: '',
						owner: 'ti',
						deadline: '2026-09-01',
						residual_consequence: 1,
						residual_probability: 1
					}
				}
			})
		).toBe(false);
		expect(
			canSubmit(trEx, {
				rows: {
					r1: {
						option: 'accept',
						control_id: '',
						owner: 'ti',
						deadline: '2026-09-01',
						residual_consequence: 2,
						residual_probability: 2
					}
				}
			})
		).toBe(true);
	});

	it('audit_checklist, nonconformity_form y competence_matrix exigen campos completos', () => {
		const auditEx: Exercise = {
			kind: 'audit_checklist',
			pass_score: 70,
			spec: {
				prompt: 'p',
				scenario: 's',
				verdicts: opts('conforme', 'nc_mayor'),
				items: [
					{
						id: 'i1',
						clause_ref: '7.2',
						requirement_title: 'Competencia',
						observed_context: 'ok',
						questions: opts('q1'),
						evidences: opts('e1')
					}
				]
			}
		};
		expect(canSubmit(auditEx, initialAnswer(auditEx))).toBe(false);
		expect(
			canSubmit(auditEx, {
				items: { i1: { question_id: 'q1', evidence_id: 'e1', verdict: 'conforme' } }
			})
		).toBe(true);

		const ncEx: Exercise = {
			kind: 'nonconformity_form',
			pass_score: 70,
			spec: {
				prompt: 'p',
				scenario: 's',
				documents: opts('pims-alcance'),
				positions: opts('dpo'),
				cases: [
					{
						id: 'c1',
						title: 'Hallazgo',
						detection_context: 'ctx',
						detection_date: '2026-07-01',
						correction_options: opts('c'),
						root_cause_options: opts('r'),
						action_options: opts('a'),
						verification_options: opts('v')
					}
				]
			}
		};
		expect(
			canSubmit(ncEx, {
				cases: {
					c1: {
						correction: 'c',
						root_cause: 'r',
						requires_action: true,
						action: 'a',
						responsible: 'dpo',
						implementation_date: '2026-07-10',
						verification_date: '2026-08-10',
						verification: 'v',
						doc_change: true,
						affected_document: ''
					}
				}
			})
		).toBe(false);
		expect(
			canSubmit(ncEx, {
				cases: {
					c1: {
						correction: 'c',
						root_cause: 'r',
						requires_action: true,
						action: 'a',
						responsible: 'dpo',
						implementation_date: '2026-07-10',
						verification_date: '2026-08-10',
						verification: 'v',
						doc_change: false,
						affected_document: ''
					}
				}
			})
		).toBe(true);

		const compEx: Exercise = {
			kind: 'competence_matrix',
			pass_score: 70,
			spec: {
				prompt: 'p',
				scenario: 's',
				competencies: opts('c1'),
				trainings: opts('t1'),
				evidences: opts('e1'),
				evaluators: opts('dpo'),
				rows: [{ id: 'r1', position_title: 'DPO', role_summary: 'Rol' }]
			}
		};
		expect(
			canSubmit(compEx, {
				rows: {
					r1: { competency_id: 'c1', training_id: 't1', evidence_id: 'e1', evaluator_id: '' }
				}
			})
		).toBe(false);
		expect(
			canSubmit(compEx, {
				rows: {
					r1: { competency_id: 'c1', training_id: 't1', evidence_id: 'e1', evaluator_id: 'dpo' }
				}
			})
		).toBe(true);
	});
});
