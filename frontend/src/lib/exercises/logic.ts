import type { Answer, Exercise, SoaDecision } from './types';

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
	}
}

export function canSubmit(exercise: Exercise, answer: Answer): boolean {
	const { done, total } = completion(exercise, answer);
	return done === total;
}
