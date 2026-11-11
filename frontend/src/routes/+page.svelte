<script lang="ts">
	import type { PageProps } from './$types';

	let { data }: PageProps = $props();

	const label = { up: 'Operativo', down: 'Sin conexión', unknown: 'Desconocido' } as const;
</script>

<h1>Capacitación de Auditores Internos · UNSA</h1>
<p class="lead">
	Cuatro rutas — Sensibilización, Interpretación, Implementación y Auditor — para conocer la
	universidad y auditarla con criterio.
</p>

{#if data.user}
	<section class="card" aria-labelledby="hola">
		<h2 id="hola">Hola, {data.user.full_name}</h2>
		<p><a href="/routes">Continúa con tus rutas de capacitación</a> o explora tu universidad:</p>
		<ul>
			<li><a href="/university">Organigrama y cargos</a></li>
			<li><a href="/systems">Sistemas y dueños de datos</a></li>
		</ul>
	</section>
{:else}
	<section class="card" aria-labelledby="acceso">
		<h2 id="acceso">Acceso</h2>
		<p><a href="/login">Inicia sesión</a> o <a href="/register">crea tu cuenta</a> para continuar.</p>
	</section>
{/if}

<section class="card estado" aria-labelledby="estado-titulo">
	<h2 id="estado-titulo">Estado del sistema</h2>
	<ul>
		<li>
			API: <strong class={data.status.api} data-testid="api-status">{label[data.status.api]}</strong>
		</li>
		<li>
			Base de datos:
			<strong class={data.status.database} data-testid="db-status"
				>{label[data.status.database]}</strong
			>
		</li>
	</ul>
</section>

<style>
	.lead {
		color: var(--muted);
		max-width: 60ch;
	}

	.card + .card {
		margin-top: 16px;
	}

	ul {
		margin: 0;
		padding-left: 1.2rem;
	}

	.up {
		color: var(--ok);
	}

	.down {
		color: var(--danger);
	}

	.unknown {
		color: var(--warn);
	}
</style>
