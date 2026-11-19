<script lang="ts">
	import { enhance } from '$app/forms';
	import { untrack } from 'svelte';
	import './doc.css';
	import AuditChecklist from './AuditChecklist.svelte';
	import CompetenceMatrix from './CompetenceMatrix.svelte';
	import DocumentForm from './DocumentForm.svelte';
	import Matching from './Matching.svelte';
	import NonconformityForm from './NonconformityForm.svelte';
	import Ordering from './Ordering.svelte';
	import RadioGroup from './RadioGroup.svelte';
	import RiskTable from './RiskTable.svelte';
	import SoaForm from './SoaForm.svelte';
	import TreatmentTable from './TreatmentTable.svelte';
	import { canSubmit, completion, initialAnswer } from './logic';
	import type {
		Answer,
		AttemptResult,
		AuditChecklistAnswer,
		CompetenceMatrixAnswer,
		DocumentFormAnswer,
		Exercise,
		NonconformityFormAnswer,
		RiskTableAnswer,
		SoaDecision,
		TreatmentTableAnswer
	} from './types';

	let {
		exercise,
		result = null,
		error = null
	}: { exercise: Exercise; result?: AttemptResult | null; error?: string | null } = $props();

	let answer = $state<Answer>(untrack(() => initialAnswer(exercise)));
	let sending = $state(false);

	const progress = $derived(completion(exercise, answer));
	const feedbackById = $derived(Object.fromEntries((result?.items ?? []).map((i) => [i.id, i])));
</script>

<form
	method="POST"
	use:enhance={() => {
		sending = true;
		return async ({ update }) => {
			await update({ reset: false });
			sending = false;
		};
	}}
>
	<p class="prompt">{exercise.spec.prompt}</p>

	{#if exercise.kind === 'soa_form'}
		<SoaForm
			spec={exercise.spec}
			answer={answer as { decisions: Record<string, SoaDecision> }}
			feedback={result?.items ?? []}
		/>
	{:else if exercise.kind === 'ordering'}
		<Ordering
			spec={exercise.spec}
			answer={answer as { order: string[] }}
			feedback={result?.items ?? []}
		/>
	{:else if exercise.kind === 'matching'}
		<Matching
			spec={exercise.spec}
			answer={answer as { assignments: Record<string, string> }}
			feedback={result?.items ?? []}
		/>
	{:else if exercise.kind === 'single_choice'}
		{@const a = answer as { choice: string }}
		<RadioGroup
			name="choice"
			legend="Elige una opción"
			options={exercise.spec.options}
			value={a.choice}
			onselect={(id) => (a.choice = id)}
			feedback={feedbackById['choice']}
		/>
	{:else if exercise.kind === 'quiz'}
		{@const a = answer as { answers: Record<string, string> }}
		{#each exercise.spec.questions as question, index (question.id)}
			<RadioGroup
				name={`q-${question.id}`}
				legend={`${index + 1}. ${question.prompt}`}
				options={question.options}
				value={a.answers[question.id]}
				onselect={(id) => (a.answers[question.id] = id)}
				feedback={feedbackById[question.id]}
			/>
		{/each}
	{:else if exercise.kind === 'branching'}
		{@const a = answer as { choices: Record<string, string> }}
		{#each exercise.spec.steps as step, index (step.id)}
			<RadioGroup
				name={`s-${step.id}`}
				legend={`Situación ${index + 1}: ${step.situation}`}
				options={step.options}
				value={a.choices[step.id]}
				onselect={(id) => (a.choices[step.id] = id)}
				feedback={feedbackById[step.id]}
			/>
		{/each}
	{:else if exercise.kind === 'document_form'}
		<DocumentForm
			spec={exercise.spec}
			answer={answer as DocumentFormAnswer}
			feedback={result?.items ?? []}
		/>
	{:else if exercise.kind === 'risk_table'}
		<RiskTable
			spec={exercise.spec}
			answer={answer as RiskTableAnswer}
			feedback={result?.items ?? []}
		/>
	{:else if exercise.kind === 'treatment_table'}
		<TreatmentTable
			spec={exercise.spec}
			answer={answer as TreatmentTableAnswer}
			feedback={result?.items ?? []}
		/>
	{:else if exercise.kind === 'audit_checklist'}
		<AuditChecklist
			spec={exercise.spec}
			answer={answer as AuditChecklistAnswer}
			feedback={result?.items ?? []}
		/>
	{:else if exercise.kind === 'nonconformity_form'}
		<NonconformityForm
			spec={exercise.spec}
			answer={answer as NonconformityFormAnswer}
			feedback={result?.items ?? []}
		/>
	{:else if exercise.kind === 'competence_matrix'}
		<CompetenceMatrix
			spec={exercise.spec}
			answer={answer as CompetenceMatrixAnswer}
			feedback={result?.items ?? []}
		/>
	{/if}

	<input type="hidden" name="answer" value={JSON.stringify(answer)} />

	{#if error}<p class="error" role="alert" data-testid="attempt-error">{error}</p>{/if}

	{#if result}
		<div
			class="result"
			class:pass={result.passed}
			role="status"
			data-testid="attempt-result"
			data-passed={result.passed}
		>
			<strong>Puntaje: {result.score} %</strong>
			— {result.passed ? 'Aprobado' : `No aprobado (mínimo ${result.pass_score} %)`}.
			{#if result.attempt_number}(Intento {result.attempt_number}){/if}
			{#if !result.passed}Revisa la retroalimentación y vuelve a intentarlo.{/if}
		</div>

		{#if !result.passed && result.solution_revealed && result.solution_guide?.length}
			<section class="doc-guide" aria-labelledby="guide-title" data-testid="solution-guide">
				<h3 id="guide-title">Guía de solución (intentos de práctica agotados)</h3>
				<p class="doc-help">
					Aplica estos criterios en los ítems pendientes y vuelve a enviar para aprobar el módulo.
				</p>
				<ul>
					{#each result.solution_guide as guide (guide.id)}
						<li><strong>{guide.label}:</strong> {guide.expected_summary}</li>
					{/each}
				</ul>
			</section>
		{/if}
	{/if}

	<div class="actions">
		<button type="submit" disabled={!canSubmit(exercise, answer) || sending}>
			{sending ? 'Enviando…' : result ? 'Enviar de nuevo' : 'Enviar respuesta'}
		</button>
		<span class="count">Respondidas: {progress.done}/{progress.total}</span>
	</div>
</form>

<style>
	.prompt {
		font-weight: 600;
		margin-top: 0;
	}

	.actions {
		display: flex;
		align-items: center;
		gap: 14px;
	}

	button {
		background: var(--primary);
		color: var(--primary-contrast);
		border: none;
		border-radius: 8px;
		padding: 10px 16px;
		font: inherit;
		cursor: pointer;
	}

	button:disabled {
		opacity: 0.5;
		cursor: default;
	}

	.count {
		color: var(--muted);
		font-size: 0.85rem;
	}

	.result {
		border: 1px solid var(--danger);
		background: #fdf4f3;
		border-radius: 8px;
		padding: 10px 14px;
		margin-bottom: 12px;
	}

	.result.pass {
		border-color: var(--ok);
		background: #f2faf5;
	}

	.error {
		color: var(--danger);
	}
</style>
