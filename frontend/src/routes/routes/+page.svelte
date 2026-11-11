<script lang="ts">
	import StatusBadge from '../../lib/StatusBadge.svelte';
	import type { PageProps } from './$types';

	let { data }: PageProps = $props();
	const titles = $derived(
		Object.fromEntries((data.listing?.routes ?? []).map((route) => [route.code, route.title]))
	);
</script>

<h1>Mis rutas de capacitación</h1>

{#if data.listing}
	<p class="lead">
		Cuatro rutas en secuencia. Horas acreditadas:
		<strong data-testid="total-hours">{data.listing.total_hours_credited} h</strong>
		de {data.listing.routes.reduce((sum, route) => sum + route.hours, 0)} h.
	</p>

	<div class="grid">
		{#each data.listing.routes as route (route.code)}
			<article class="card" data-testid={`route-${route.code}`}>
				<header>
					<span class="step">Ruta {route.order}</span>
					<StatusBadge status={route.status} />
				</header>
				<h2>{route.title}</h2>
				<p class="muted">{route.description}</p>
				<p class="meta">
					{route.hours} h previstas · {route.modules_total} módulo(s) disponible(s)
					{#if route.modules_planned > 0}· {route.modules_planned} en preparación{/if}
				</p>

				{#if route.modules_total > 0}
					<progress value={route.modules_completed} max={route.modules_total}></progress>
					<p class="meta">
						{route.modules_completed}/{route.modules_total} módulos · {route.hours_credited} h acreditadas
					</p>
				{:else}
					<p class="meta">Contenido en preparación.</p>
				{/if}

				{#if route.status === 'locked' && route.prerequisite_code}
					<p class="meta">Requiere aprobar: {titles[route.prerequisite_code]}.</p>
				{:else}
					<a class="button" href={`/routes/${route.code}`}>
						{route.status === 'available' ? 'Ver ruta' : route.status === 'completed' ? 'Repasar' : 'Continuar'}
					</a>
				{/if}
			</article>
		{/each}
	</div>
{:else}
	<p class="card">No se pudieron cargar las rutas. Verifica que el backend esté activo.</p>
{/if}

<style>
	.lead {
		color: var(--muted);
	}

	.grid {
		display: grid;
		gap: 16px;
		grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
	}

	header {
		display: flex;
		justify-content: space-between;
		align-items: center;
	}

	.step {
		font-size: 0.8rem;
		color: var(--muted);
		text-transform: uppercase;
		letter-spacing: 0.04em;
	}

	h2 {
		margin: 8px 0;
		font-size: 1.15rem;
	}

	.muted,
	.meta {
		color: var(--muted);
		font-size: 0.9rem;
		margin: 6px 0;
	}

	progress {
		width: 100%;
		height: 8px;
	}

	.button {
		display: inline-block;
		margin-top: 8px;
		background: var(--primary);
		color: var(--primary-contrast);
		text-decoration: none;
		padding: 8px 14px;
		border-radius: 8px;
	}
</style>
