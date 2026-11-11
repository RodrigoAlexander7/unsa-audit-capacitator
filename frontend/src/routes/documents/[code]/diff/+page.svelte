<script lang="ts">
	import DiffView from '../../../../lib/DiffView.svelte';
	import type { PageProps } from './$types';

	let { data }: PageProps = $props();
</script>

<p class="crumb"><a href={`/documents/${data.code}`}>← {data.code}</a></p>
<h1>Diferencias entre versiones</h1>

<form method="GET" class="card picker">
	<label>
		Desde
		<select name="from">
			{#each data.versions as version (version.number)}
				<option value={version.number} selected={version.number === data.from}
					>v{version.number} — {version.message}</option
				>
			{/each}
		</select>
	</label>
	<label>
		Hasta
		<select name="to">
			{#each data.versions as version (version.number)}
				<option value={version.number} selected={version.number === data.to}
					>v{version.number} — {version.message}</option
				>
			{/each}
		</select>
	</label>
	<button type="submit">Comparar</button>
</form>

{#if data.diff}
	<h2 data-testid="diff-title">v{data.diff.from_version} → v{data.diff.to_version}</h2>
	<DiffView diff={data.diff} />
{:else if data.notFound}
	<p class="card">Alguna de las versiones elegidas no existe.</p>
{:else}
	<p class="card">No se pudo calcular la diferencia.</p>
{/if}

<style>
	.crumb {
		margin: 0 0 8px;
	}

	.picker {
		display: flex;
		gap: 14px;
		align-items: end;
		flex-wrap: wrap;
		margin: 16px 0;
	}

	label {
		display: grid;
		gap: 4px;
		font-size: 0.9rem;
		min-width: 220px;
	}

	select {
		padding: 8px;
		border: 1px solid var(--border);
		border-radius: 6px;
		font: inherit;
		background: #fff;
	}

	button {
		background: var(--primary);
		color: var(--primary-contrast);
		border: none;
		border-radius: 8px;
		padding: 9px 16px;
		font: inherit;
		cursor: pointer;
	}

	h2 {
		font-size: 1.1rem;
	}
</style>
