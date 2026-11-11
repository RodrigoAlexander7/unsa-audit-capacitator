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

/** Ejercicio publico (sin soluciones) tal como lo entrega el API. */
export type Exercise =
	| { kind: 'soa_form'; pass_score: number; spec: SoaFormSpec }
	| { kind: 'ordering'; pass_score: number; spec: OrderingSpec }
	| { kind: 'matching'; pass_score: number; spec: MatchingSpec }
	| { kind: 'single_choice'; pass_score: number; spec: SingleChoiceSpec }
	| { kind: 'quiz'; pass_score: number; spec: QuizSpec }
	| { kind: 'branching'; pass_score: number; spec: BranchingSpec };

export type SoaDecision = { applies: boolean | null; reason: string };

export type Answer =
	| { decisions: Record<string, SoaDecision> }
	| { order: string[] }
	| { assignments: Record<string, string> }
	| { choice: string }
	| { answers: Record<string, string> }
	| { choices: Record<string, string> };

export type ItemFeedback = { id: string; correct: boolean; feedback: string };

export type AttemptResult = {
	score: number;
	passed: boolean;
	pass_score: number;
	items: ItemFeedback[];
	module_completed: boolean;
	route_completed: boolean;
};
