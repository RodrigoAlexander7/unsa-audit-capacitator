<script lang="ts">
	import StatusBadge from '../../../lib/StatusBadge.svelte';
	import type { PageProps } from './$types';

	let { data, form }: PageProps = $props();
	const route = $derived(data.detail.route);
	const modules = $derived(data.detail.modules);
	const enrolled = $derived(route.status === 'in_progress' || route.status === 'completed');

	const MODULE_LABEL = { locked: 'Bloqueado', available: 'Disponible', completed: 'Completado' };
</script>

<p class="crumb"><a href="/routes">← Mis rutas</a></p>
<h1>{route.title} <StatusBadge status={route.status} /></h1>
<p class="lead">{route.description}</p>
<p class="meta">
	{route.hours} h · {route.hours_credited} h acreditadas · {route.modules_completed}/{route.modules_total}
	módulos
</p>

{#if form?.error}<p class="error" role="alert">{form.error}</p>{/if}

{#if route.status === 'locked'}
	<p class="card">Debes aprobar la ruta anterior para matricularte en esta.</p>
{:else if route.status === 'available'}
	<form method="POST" action="?/enroll" class="card">
		<p>Aún no estás matriculado en esta ruta.</p>
		<button type="submit">Matricularme</button>
	</form>
{/if}

{#if route.modules_total === 0 && enrolled}
	<p class="card">Esta ruta todavía no tiene módulos publicados. Estará disponible próximamente.</p>
{/if}

{#if modules.length}
	<ol class="modules">
		{#each modules as module (module.id)}
			<li class={module.status} data-testid={`module-${module.order}`}>
				<div class="main">
					{#if module.status !== 'locked'}
						<a href={`/routes/${route.code}/${module.id}`}>{module.order}. {module.title}</a>
					{:else}
						<span>{module.order}. {module.title}</span>
					{/if}
					<span class="meta">
						{module.minutes} min{module.is_final ? ' · evaluación final' : ''}
						{#if module.best_score !== null}· mejor puntaje {module.best_score} %{/if}
					</span>
				</div>
				<span class="state">{MODULE_LABEL[module.status]}</span>
			</li>
		{/each}
	</ol>
{/if}

<style>
	.crumb {
		margin: 0 0 8px;
	}

	.lead,
	.meta {
		color: var(--muted);
	}

	.meta {
		font-size: 0.9rem;
	}

	h1 {
		display: flex;
		gap: 12px;
		align-items: center;
		flex-wrap: wrap;
	}

	.card {
		margin: 16px 0;
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

	.modules {
		list-style: none;
		padding: 0;
		margin: 20px 0 0;
		display: grid;
		gap: 8px;
	}

	li {
		display: flex;
		justify-content: space-between;
		align-items: center;
		gap: 12px;
		background: var(--surface);
		border: 1px solid var(--border);
		border-radius: 8px;
		padding: 12px 14px;
	}

	li.locked {
		opacity: 0.6;
	}

	li.completed {
		border-color: #b4dcc2;
		background: #f7fcf9;
	}

	.main {
		display: grid;
		gap: 2px;
	}

	.state {
		font-size: 0.8rem;
		color: var(--muted);
		white-space: nowrap;
	}

	.error {
		color: var(--danger);
	}
</style>
