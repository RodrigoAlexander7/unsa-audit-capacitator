export type Opt = { id: string; label: string };

export type OrderingSpec = { prompt: string; items: Opt[] };
export type MatchingSpec = { prompt: string; left: Opt[]; right: Opt[] };
export type SingleChoiceSpec = { prompt: string; options: Opt[] };
export type QuizSpec = {
	prompt: string;
	questions: { id: string; prompt: string; options: Opt[] }[];
};
export type BranchingSpec = {
	prompt: string;
	steps: { id: string; situation: string; options: Opt[] }[];
};

export type SoaFormSpec = {
	prompt: string;
	scenario: string;
	reasons: Opt[];
	controls: Opt[];
};

export type DocFieldType =
	'text' | 'textarea' | 'date' | 'select' | 'multiselect' | 'position' | 'reference';

export type DocFieldSpec = {
	id: string;
	label: string;
	type: DocFieldType;
	required: boolean;
	help?: string;
	placeholder?: string;
	options?: Opt[];
};

export type DocSectionSpec = {
	id: string;
	title: string;
	description?: string;
	fields: DocFieldSpec[];
};

export type DocumentFormSpec = {
	prompt: string;
	scenario: string;
	document_title: string;
	sections: DocSectionSpec[];
};

export type RiskRowSpec = {
	id: string;
	asset: string;
	asset_owner: string;
	data_categories: string[];
	existing_controls: string;
	threat: string;
	vulnerability: string;
	risk_owner: string;
	threat_options?: Opt[];
	vulnerability_options?: Opt[];
	risk_owner_options?: Opt[];
};

export type RiskTableSpec = {
	prompt: string;
	scenario: string;
	threshold: number;
	rows: RiskRowSpec[];
};

export type TreatmentRowSpec = {
	id: string;
	asset: string;
	threat: string;
	vulnerability: string;
	initial_consequence: number;
	initial_probability: number;
	initial_risk: number;
	risk_owner: string;
};

export type TreatmentTableSpec = {
	prompt: string;
	scenario: string;
	options: Opt[];
	soa_controls: Opt[];
	owners: Opt[];
	rows: TreatmentRowSpec[];
};

export type AuditItemSpec = {
	id: string;
	clause_ref: string;
	requirement_title: string;
	observed_context: string;
	questions: Opt[];
	evidences: Opt[];
};

export type AuditChecklistSpec = {
	prompt: string;
	scenario: string;
	verdicts: Opt[];
	items: AuditItemSpec[];
};

export type NonconformityCaseSpec = {
	id: string;
	title: string;
	detection_context: string;
	detection_date: string;
	correction_options: Opt[];
	root_cause_options: Opt[];
	action_options: Opt[];
	verification_options: Opt[];
};

export type NonconformityFormSpec = {
	prompt: string;
	scenario: string;
	documents: Opt[];
	positions: Opt[];
	cases: NonconformityCaseSpec[];
};

export type CompetenceRowSpec = {
	id: string;
	position_title: string;
	role_summary: string;
};

export type CompetenceMatrixSpec = {
	prompt: string;
	scenario: string;
	competencies: Opt[];
	trainings: Opt[];
	evidences: Opt[];
	evaluators?: Opt[];
	rows: CompetenceRowSpec[];
};

/** Ejercicio publico (sin soluciones) tal como lo entrega el API. */
export type Exercise =
	| { kind: 'soa_form'; pass_score: number; spec: SoaFormSpec }
	| { kind: 'ordering'; pass_score: number; spec: OrderingSpec }
	| { kind: 'matching'; pass_score: number; spec: MatchingSpec }
	| { kind: 'single_choice'; pass_score: number; spec: SingleChoiceSpec }
	| { kind: 'quiz'; pass_score: number; spec: QuizSpec }
	| { kind: 'branching'; pass_score: number; spec: BranchingSpec }
	| { kind: 'document_form'; pass_score: number; spec: DocumentFormSpec }
	| { kind: 'risk_table'; pass_score: number; spec: RiskTableSpec }
	| { kind: 'treatment_table'; pass_score: number; spec: TreatmentTableSpec }
	| { kind: 'audit_checklist'; pass_score: number; spec: AuditChecklistSpec }
	| { kind: 'nonconformity_form'; pass_score: number; spec: NonconformityFormSpec }
	| { kind: 'competence_matrix'; pass_score: number; spec: CompetenceMatrixSpec };

export type SoaDecision = { applies: boolean | null; reason: string };

export type DocumentFormAnswer = { fields: Record<string, string | string[]> };

export type RiskRowAnswer = {
	consequence: number | null;
	probability: number | null;
	threat?: string;
	vulnerability?: string;
	risk_owner?: string;
};
export type RiskTableAnswer = { rows: Record<string, RiskRowAnswer> };

export type TreatmentRowAnswer = {
	option: string;
	control_id: string;
	owner: string;
	deadline: string;
	residual_consequence: number | null;
	residual_probability: number | null;
};
export type TreatmentTableAnswer = { rows: Record<string, TreatmentRowAnswer> };

export type AuditItemAnswer = { question_id: string; evidence_id: string; verdict: string };
export type AuditChecklistAnswer = { items: Record<string, AuditItemAnswer> };

export type NonconformityCaseAnswer = {
	correction: string;
	root_cause: string;
	requires_action: boolean | null;
	action: string;
	responsible: string;
	implementation_date: string;
	verification_date: string;
	verification: string;
	doc_change: boolean | null;
	affected_document: string;
};
export type NonconformityFormAnswer = { cases: Record<string, NonconformityCaseAnswer> };

export type CompetenceRowAnswer = {
	competency_id: string;
	training_id: string;
	evidence_id: string;
	evaluator_id?: string;
};
export type CompetenceMatrixAnswer = { rows: Record<string, CompetenceRowAnswer> };

export type Answer =
	| { decisions: Record<string, SoaDecision> }
	| { order: string[] }
	| { assignments: Record<string, string> }
	| { choice: string }
	| { answers: Record<string, string> }
	| { choices: Record<string, string> }
	| DocumentFormAnswer
	| RiskTableAnswer
	| TreatmentTableAnswer
	| AuditChecklistAnswer
	| NonconformityFormAnswer
	| CompetenceMatrixAnswer;

export type ItemFeedback = { id: string; correct: boolean; feedback: string };

export type SolutionGuideItem = { id: string; label: string; expected_summary: string };

export type AttemptResult = {
	score: number;
	passed: boolean;
	pass_score: number;
	items: ItemFeedback[];
	module_completed: boolean;
	route_completed: boolean;
	attempt_number?: number;
	solution_revealed?: boolean;
	solution_guide?: SolutionGuideItem[] | null;
};
