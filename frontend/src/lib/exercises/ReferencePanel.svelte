<script lang="ts">
	let { title, html }: { title: string; html: string } = $props();
	let expanded = $state(true);
</script>

<aside class="card ref-panel" aria-labelledby="ref-title" data-testid="reference-panel">
	<div class="ref-head">
		<div>
			<span class="ref-eyebrow">Ejemplo resuelto (UNSA)</span>
			<h2 id="ref-title">{title}</h2>
		</div>
		<button
			type="button"
			class="ref-toggle"
			aria-expanded={expanded}
			aria-controls="ref-body"
			onclick={() => (expanded = !expanded)}
		>
			{expanded ? 'Ocultar' : 'Mostrar'}
		</button>
	</div>

	{#if expanded}
		<!-- svelte-ignore a11y_no_noninteractive_tabindex -->
		<div id="ref-body" class="ref-body" tabindex="0" role="region" aria-labelledby="ref-title">
			<!-- eslint-disable-next-line svelte/no-at-html-tags -- contenido propio del repositorio -->
			{@html html}
		</div>
	{/if}
</aside>

<style>
	.ref-panel {
		background: #fcfdff;
	}

	.ref-head {
		display: flex;
		justify-content: space-between;
		align-items: flex-start;
		gap: 12px;
		margin-bottom: 10px;
	}

	.ref-eyebrow {
		display: inline-block;
		background: #e7eefb;
		color: var(--primary);
		border-radius: 999px;
		padding: 2px 10px;
		font-size: 0.78rem;
		font-weight: 600;
		margin-bottom: 6px;
	}

	h2 {
		margin: 0;
		font-size: 1.1rem;
	}

	.ref-toggle {
		background: var(--surface);
		color: var(--primary);
		border: 1px solid var(--border);
		border-radius: 6px;
		padding: 5px 10px;
		font: inherit;
		font-size: 0.85rem;
		cursor: pointer;
	}

	.ref-toggle:focus-visible,
	.ref-body:focus-visible {
		outline: 2px solid var(--primary);
		outline-offset: 2px;
	}

	.ref-body {
		font-size: 0.92rem;
		overflow-x: auto;
	}

	.ref-body :global(h1),
	.ref-body :global(h2) {
		font-size: 1rem;
		margin: 12px 0 6px;
	}

	.ref-body :global(table) {
		width: 100%;
		border-collapse: collapse;
		font-size: 0.85rem;
		margin: 10px 0;
	}

	.ref-body :global(th),
	.ref-body :global(td) {
		border: 1px solid var(--border);
		padding: 6px 8px;
		text-align: left;
	}

	.ref-body :global(th) {
		background: var(--bg);
	}

	.ref-body :global(blockquote) {
		margin: 10px 0;
		padding: 4px 12px;
		border-left: 3px solid var(--border);
		color: var(--muted);
	}

	@media (min-width: 1024px) {
		.ref-panel {
			position: sticky;
			top: 16px;
		}

		.ref-body {
			max-height: calc(100vh - 130px);
			overflow-y: auto;
		}
	}
</style>
