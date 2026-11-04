<script lang="ts">
	let { text }: { text: string } = $props();

	const lines = $derived(
		text.split('\n').map((line) => ({
			kind: line.startsWith('+ ') ? 'add' : line.startsWith('- ') ? 'del' : 'plain',
			text: line
		}))
	);
</script>

{#each lines as line, index (index)}
	<span class={`line ${line.kind}`}>
		{#if line.kind === 'add'}<span class="sr">Añadido: </span>{/if}
		{#if line.kind === 'del'}<span class="sr">Eliminado: </span>{/if}
		{line.text}
	</span>
{/each}

<style>
	.line {
		display: block;
		white-space: pre-wrap;
	}

	.add,
	.del {
		font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
		font-size: 0.9rem;
		font-weight: 400;
		padding: 1px 8px;
		border-left: 3px solid;
	}

	.add {
		background: #e9f7ee;
		border-color: var(--ok);
	}

	.del {
		background: #fdeceb;
		border-color: var(--danger);
	}

	.sr {
		position: absolute;
		width: 1px;
		height: 1px;
		overflow: hidden;
		clip: rect(0 0 0 0);
		white-space: nowrap;
	}
</style>
