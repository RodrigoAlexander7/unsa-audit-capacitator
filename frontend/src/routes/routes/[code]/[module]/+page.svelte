<script lang="ts">
	import ExerciseForm from '../../../../lib/exercises/ExerciseForm.svelte';
	import ReferencePanel from '../../../../lib/exercises/ReferencePanel.svelte';
	import type { PageProps } from './$types';

	let { data, form }: PageProps = $props();
	const mod = $derived(data.module);
	const result = $derived(form && 'result' in form ? form.result : null);
	const error = $derived(form && 'error' in form ? form.error : null);
</script>

<p class="crumb"><a href={`/routes/${mod.route_code}`}>← {data.routeTitle}</a></p>
<h1>{mod.title}</h1>
<p class="meta">
	{mod.minutes} min{mod.is_final ? ' · evaluación final' : ''}
	{#if mod.status === 'completed'}· <strong class="done">Completado</strong>{/if}
	{#if mod.best_score !== null}· mejor puntaje {mod.best_score} %{/if}
</p>

<article class="card lesson" data-testid="lesson">
	<!-- eslint-disable-next-line svelte/no-at-html-tags -- contenido propio del repositorio -->
	{@html data.lessonHtml}
</article>

{#if mod.exercise && data.referenceHtml && mod.reference}
	<div class="practice-grid" data-testid="practice-side-by-side">
		<ReferencePanel title={mod.reference.title} html={data.referenceHtml} />
		<section class="card exercise" aria-labelledby="ej">
			<h2 id="ej">Tu documento · Ejercicio</h2>
			{#key mod.id}
				<ExerciseForm exercise={mod.exercise} {result} {error} />
			{/key}
		</section>
	</div>
{:else if mod.exercise}
	<section class="card exercise" aria-labelledby="ej">
		<h2 id="ej">Ejercicio</h2>
		{#key mod.id}
			<ExerciseForm exercise={mod.exercise} {result} {error} />
		{/key}
	</section>
{/if}

{#if result?.route_completed}
	<p class="banner" role="status" data-testid="route-completed">
		🎉 ¡Ruta aprobada! <a href="/routes">Ver mis rutas</a>
	</p>
{:else if mod.status === 'completed' && data.nextModuleId}
	<p class="banner">
		<a href={`/routes/${mod.route_code}/${data.nextModuleId}`} data-testid="next-module"
			>Siguiente módulo →</a
		>
	</p>
{:else if mod.status === 'completed'}
	<p class="banner"><a href={`/routes/${mod.route_code}`}>Volver a la ruta</a></p>
{/if}

<style>
	.crumb {
		margin: 0 0 8px;
	}

	.meta {
		color: var(--muted);
	}

	.done {
		color: var(--ok);
	}

	.card {
		margin: 16px 0;
	}

	.practice-grid {
		display: grid;
		gap: 16px;
		margin: 16px 0;
	}

	.practice-grid :global(.card) {
		margin: 0;
	}

	@media (min-width: 1024px) {
		.practice-grid {
			grid-template-columns: minmax(0, 1fr) minmax(0, 1.15fr);
			align-items: start;
		}
	}

	.lesson :global(h1) {
		font-size: 1.4rem;
		margin-top: 0;
	}

	.lesson :global(table) {
		border-collapse: collapse;
		width: 100%;
		margin: 12px 0;
		font-size: 0.95rem;
	}

	.lesson :global(th),
	.lesson :global(td) {
		border: 1px solid var(--border);
		padding: 6px 10px;
		text-align: left;
	}

	.lesson :global(blockquote) {
		margin: 12px 0;
		padding: 4px 14px;
		border-left: 3px solid var(--border);
		color: var(--muted);
	}

	.exercise h2 {
		margin-top: 0;
	}

	.banner {
		background: #f2faf5;
		border: 1px solid #b4dcc2;
		border-radius: 8px;
		padding: 12px 16px;
	}
</style>
