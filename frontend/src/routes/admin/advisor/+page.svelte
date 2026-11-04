<script lang="ts">
	import { enhance } from '$app/forms';
	import { formatDate } from '../../../lib/format';
	import { renderMarkdown } from '../../../lib/markdown';
	import type { PageProps } from './$types';

	let { data, form }: PageProps = $props();

	let question = $state('');
	let asking = $state(false);
	const answer = $derived(form && 'answer' in form ? form.answer : null);
	const error = $derived(form && 'error' in form ? form.error : null);

	const EXAMPLES = [
		'¿Cómo están los alumnos de sensibilización?',
		'¿Qué módulos debería reforzar primero y por qué?',
		'¿En qué requisitos del PIMS fallan más los participantes en las evaluaciones?',
		'¿Hay participantes estancados? ¿Qué ajustes propones?'
	];
</script>

<p class="crumb"><a href="/admin">← Panel</a></p>
<h1>Asesor IA</h1>
<p class="lead">
	Pregunta en lenguaje natural. El asesor (<code>agy</code>) recibe solo estadísticas agregadas y
	anonimizadas —nunca nombres ni correos— y propone ajustes al plan de enseñanza.
	<a href="/admin/advisor/snapshot.json" data-sveltekit-reload data-testid="snapshot-link"
		>Descargar el snapshot</a
	> para consultarlo manualmente en una terminal.
</p>

<form
	method="POST"
	class="card"
	use:enhance={() => {
		asking = true;
		return async ({ update }) => {
			await update({ reset: false });
			asking = false;
		};
	}}
>
	<label for="q">Tu pregunta</label>
	<textarea
		id="q"
		name="question"
		rows="3"
		maxlength="1000"
		bind:value={question}
		placeholder="Ej.: ¿Cómo están los alumnos de sensibilización?"
	></textarea>
	<div class="examples" aria-label="Preguntas de ejemplo">
		{#each EXAMPLES as example (example)}
			<button type="button" class="chip" onclick={() => (question = example)}>{example}</button>
		{/each}
	</div>
	<div class="actions">
		<button type="submit" disabled={asking || !question.trim()}>
			{asking ? 'Consultando a la IA…' : 'Preguntar'}
		</button>
		{#if asking}<span class="meta" role="status">Puede tardar unos segundos.</span>{/if}
	</div>
</form>

{#if error}<p class="error card" role="alert" data-testid="advisor-error">{error}</p>{/if}

{#if answer}
	<section class="card answer" aria-labelledby="resp" data-testid="advisor-answer">
		<h2 id="resp">Respuesta</h2>
		<p class="meta">Pregunta: {form && 'question' in form ? form.question : ''}</p>
		<!-- eslint-disable-next-line svelte/no-at-html-tags -- renderMarkdown escapa HTML crudo -->
		<div class="md">{@html renderMarkdown(answer)}</div>
	</section>
{/if}

<h2>Historial</h2>
{#if data.history.length}
	<ul class="history" data-testid="advisor-history">
		{#each data.history as item (item.id)}
			<li class="card">
				<details>
					<summary>
						<strong>{item.question}</strong>
						<span class="meta">
							· {formatDate(item.created_at)} · {item.status === 'ok' ? 'respondida' : 'con error'} ·
							{(item.duration_ms / 1000).toFixed(1)} s
						</span>
					</summary>
					{#if item.answer}
						<!-- eslint-disable-next-line svelte/no-at-html-tags -- renderMarkdown escapa HTML crudo -->
						<div class="md">{@html renderMarkdown(item.answer)}</div>
					{:else}
						<p class="error">{item.error}</p>
					{/if}
				</details>
			</li>
		{/each}
	</ul>
{:else}
	<p class="meta">Aún no hay consultas.</p>
{/if}

<style>
	.crumb {
		margin: 0 0 8px;
	}

	.lead,
	.meta {
		color: var(--muted);
	}

	.lead {
		max-width: 75ch;
	}

	.meta {
		font-size: 0.88rem;
	}

	.card {
		margin: 16px 0;
	}

	label {
		display: block;
		font-weight: 600;
		margin-bottom: 6px;
	}

	textarea {
		width: 100%;
		padding: 10px;
		border: 1px solid var(--border);
		border-radius: 8px;
		font: inherit;
		resize: vertical;
	}

	.examples {
		display: flex;
		flex-wrap: wrap;
		gap: 8px;
		margin: 10px 0;
	}

	.chip {
		background: var(--bg);
		border: 1px solid var(--border);
		border-radius: 999px;
		padding: 4px 12px;
		font: inherit;
		font-size: 0.85rem;
		cursor: pointer;
		color: var(--primary);
	}

	.actions {
		display: flex;
		gap: 12px;
		align-items: center;
	}

	button[type='submit'] {
		background: var(--primary);
		color: var(--primary-contrast);
		border: none;
		border-radius: 8px;
		padding: 10px 18px;
		font: inherit;
		cursor: pointer;
	}

	button[type='submit']:disabled {
		opacity: 0.5;
		cursor: default;
	}

	.error {
		color: var(--danger);
	}

	.answer {
		border-color: #b8cdea;
		background: #f8fbff;
	}

	.answer h2 {
		margin-top: 0;
		font-size: 1.1rem;
	}

	.md :global(h2) {
		font-size: 1.05rem;
		margin: 14px 0 6px;
	}

	.md :global(ol),
	.md :global(ul) {
		padding-left: 1.3rem;
	}

	.history {
		list-style: none;
		padding: 0;
		margin: 0;
	}

	.history .card {
		margin: 8px 0;
		padding: 12px 16px;
	}

	summary {
		cursor: pointer;
	}
</style>
