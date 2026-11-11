<script lang="ts">
	import { PROFILE_LABEL } from '../../../lib/api';
	import RadioGroup from '../../../lib/exercises/RadioGroup.svelte';
	import type { PageProps } from './$types';

	let { data, form }: PageProps = $props();
	const attempt = $derived(data.attempt);
	const result = $derived(attempt.result);

	let answers = $state<Record<string, string>>({});
	const answered = $derived(Object.keys(answers).length);
	const total = $derived(attempt.questions.length);

	// Peor competencia primero para sugerir qué reforzar.
	const weakest = $derived(
		result ? [...result.competencies].sort((a, b) => a.percent - b.percent)[0] : null
	);
</script>

<p class="crumb"><a href="/assessment">← Evaluación</a></p>
<h1>{attempt.title}</h1>
<p class="meta">{PROFILE_LABEL[attempt.profile]} · mínimo para aprobar: {attempt.pass_score} %</p>

{#if form?.error}<p class="error" role="alert" data-testid="form-error">{form.error}</p>{/if}

{#if attempt.status === 'in_progress'}
	<form method="POST" class="card">
		{#each attempt.questions as question, index (question.id)}
			<RadioGroup
				name={`q-${question.id}`}
				legend={`${index + 1}. ${question.prompt}`}
				options={question.options}
				value={answers[question.id]}
				onselect={(id) => (answers[question.id] = id)}
			/>
		{/each}
		<input type="hidden" name="answers" value={JSON.stringify(answers)} />
		<div class="actions">
			<button type="submit" disabled={answered < total}>Enviar evaluación</button>
			<span class="meta" data-testid="answered">Respondidas: {answered}/{total}</span>
		</div>
		{#if answered < total}
			<p class="meta">Responde todas las preguntas para poder enviar.</p>
		{/if}
	</form>
{:else if result}
	<section class="card summary" class:pass={result.passed} data-testid="assessment-result">
		<p class="big">
			{result.score} % — {result.passed ? 'Aprobada' : 'No aprobada'}
		</p>
		{#if weakest && weakest.percent < 100}
			<p class="meta">
				A reforzar primero: <strong>{weakest.label}</strong> ({weakest.correct}/{weakest.total}).
			</p>
		{:else}
			<p class="meta">¡Dominas todas las competencias evaluadas!</p>
		{/if}
		<a class="button" href="/assessment">Hacer otra evaluación</a>
	</section>

	<section class="card" aria-labelledby="comp">
		<h2 id="comp">Por competencia</h2>
		<ul class="bars" data-testid="competencies">
			{#each result.competencies as group (group.key)}
				<li>
					<span class="label">{group.label}</span>
					<progress value={group.correct} max={group.total}></progress>
					<span class="pct">{group.correct}/{group.total} · {group.percent} %</span>
				</li>
			{/each}
		</ul>
	</section>

	<section class="card" aria-labelledby="req">
		<h2 id="req">Por requisito del PIMS</h2>
		<p class="meta">
			Cada pregunta se asocia a un requisito de la
			<a href="/documents/pims">información documentada del PIMS</a>. Las cláusulas deben verificarse
			según la edición de la norma.
		</p>
		<ul class="bars" data-testid="requirements">
			{#each result.requirements as group (group.key)}
				<li>
					<span class="label">{group.label}</span>
					<progress value={group.correct} max={group.total}></progress>
					<span class="pct">{group.correct}/{group.total} · {group.percent} %</span>
				</li>
			{/each}
		</ul>
	</section>

	<section class="card" aria-labelledby="det">
		<h2 id="det">Corrección</h2>
		<ol class="items">
			{#each result.items as item (item.question_id)}
				<li class:ok={item.correct} class:bad={!item.correct}>
					<p class="q"><strong>{item.correct ? '✓' : '✗'}</strong> {item.prompt}</p>
					{#if !item.correct}
						<p class="a">
							Tu respuesta: {item.chosen_label ?? 'sin responder'}<br />
							Correcta: {item.correct_label}
						</p>
					{/if}
					<p class="e">{item.explanation}</p>
				</li>
			{/each}
		</ol>
	</section>
{/if}

<style>
	.crumb {
		margin: 0 0 8px;
	}

	.meta {
		color: var(--muted);
		font-size: 0.9rem;
	}

	.card {
		margin: 16px 0;
	}

	h2 {
		margin-top: 0;
		font-size: 1.1rem;
	}

	.actions {
		display: flex;
		gap: 14px;
		align-items: center;
	}

	button,
	.button {
		background: var(--primary);
		color: var(--primary-contrast);
		border: none;
		border-radius: 8px;
		padding: 10px 16px;
		font: inherit;
		cursor: pointer;
		text-decoration: none;
		display: inline-block;
	}

	button:disabled {
		opacity: 0.5;
		cursor: default;
	}

	.summary {
		border-color: var(--danger);
		background: #fdf4f3;
	}

	.summary.pass {
		border-color: var(--ok);
		background: #f2faf5;
	}

	.big {
		font-size: 1.5rem;
		font-weight: 700;
		margin: 0 0 6px;
	}

	.bars {
		list-style: none;
		margin: 0;
		padding: 0;
		display: grid;
		gap: 10px;
	}

	.bars li {
		display: grid;
		grid-template-columns: minmax(180px, 2fr) 3fr minmax(90px, auto);
		gap: 12px;
		align-items: center;
	}

	progress {
		width: 100%;
		height: 10px;
	}

	.pct {
		font-size: 0.85rem;
		color: var(--muted);
		white-space: nowrap;
	}

	.items {
		margin: 0;
		padding-left: 1.2rem;
		display: grid;
		gap: 14px;
	}

	.items li.ok {
		color: inherit;
	}

	.q,
	.a,
	.e {
		margin: 2px 0;
	}

	.a,
	.e {
		font-size: 0.9rem;
		color: var(--muted);
	}

	.error {
		color: var(--danger);
	}

	@media (max-width: 640px) {
		.bars li {
			grid-template-columns: 1fr;
			gap: 4px;
		}
	}
</style>
