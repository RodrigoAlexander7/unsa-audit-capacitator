<script lang="ts">
	import '../app.css';
	import favicon from '#lib/assets/favicon.svg';
	import type { LayoutProps } from './$types';

	let { data, children }: LayoutProps = $props();
</script>

<svelte:head>
	<link rel="icon" href={favicon} />
	<title>Capacitación de Auditores Internos · UNSA</title>
</svelte:head>

<div class="poc-banner" role="note">Datos ficticios – POC</div>

<header class="topbar">
	<div class="container bar">
		<a class="brand" href="/">Auditores UNSA</a>
		<nav aria-label="Principal">
			{#if data.user}
				<a href="/routes">Mis rutas</a>
				<a href="/documents">Documentos</a>
				<a href="/university">Universidad</a>
				<a href="/systems">Sistemas</a>
			{/if}
		</nav>
		<div class="session">
			{#if data.user}
				<span class="who" data-testid="session-user">{data.user.full_name}</span>
				{#if data.user.role === 'superadmin'}<span class="badge">superadmin</span>{/if}
				<form method="POST" action="/logout">
					<button type="submit" class="link">Cerrar sesión</button>
				</form>
			{:else}
				<a href="/login">Iniciar sesión</a>
				<a href="/register">Registrarse</a>
			{/if}
		</div>
	</div>
</header>

<main class="container">
	{@render children()}
</main>

<style>
	.poc-banner {
		background: #fff4d6;
		border-bottom: 1px solid #f0d58a;
		color: #6b4e00;
		text-align: center;
		font-size: 0.85rem;
		padding: 6px 12px;
	}

	.topbar {
		background: var(--surface);
		border-bottom: 1px solid var(--border);
	}

	.bar {
		display: flex;
		align-items: center;
		gap: 24px;
		min-height: 52px;
		flex-wrap: wrap;
	}

	.brand {
		font-weight: 700;
		text-decoration: none;
	}

	nav {
		display: flex;
		gap: 16px;
		flex: 1;
	}

	.session {
		display: flex;
		align-items: center;
		gap: 12px;
	}

	.session form {
		margin: 0;
	}

	.badge {
		background: #e7eefb;
		color: var(--primary);
		border-radius: 999px;
		padding: 2px 10px;
		font-size: 0.75rem;
	}

	button.link {
		background: none;
		border: none;
		padding: 0;
		color: var(--primary);
		cursor: pointer;
		font: inherit;
		text-decoration: underline;
	}

	main {
		padding-top: 32px;
		padding-bottom: 32px;
	}
</style>
