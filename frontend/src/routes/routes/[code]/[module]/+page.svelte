<script lang="ts">
	import ExerciseForm from '../../../../lib/exercises/ExerciseForm.svelte';
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

{#if mod.exercise}
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
