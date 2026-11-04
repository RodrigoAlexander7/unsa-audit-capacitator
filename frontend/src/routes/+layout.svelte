<script lang="ts">
	import '../app.css';
	import favicon from '#lib/assets/favicon.svg';
	import type { LayoutProps } from './$types';

	let { children }: LayoutProps = $props();
</script>

<svelte:head>
	<link rel="icon" href={favicon} />
	<title>Capacitación de Auditores Internos · UNSA</title>
</svelte:head>

<div class="poc-banner" role="note">Datos ficticios – POC</div>

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

	main {
		padding-top: 32px;
		padding-bottom: 32px;
	}
</style>
