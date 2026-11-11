import { describe, expect, it } from 'vitest';
import { canSubmit, completion, initialAnswer, moveItem } from './logic';
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
});
