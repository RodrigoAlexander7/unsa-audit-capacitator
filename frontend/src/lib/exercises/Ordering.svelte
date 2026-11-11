<script lang="ts">
	import { moveItem } from './logic';
	import type { ItemFeedback, OrderingSpec } from './types';

	let {
		spec,
		answer,
		feedback = []
	}: {
		spec: OrderingSpec;
		answer: { order: string[] };
		feedback?: ItemFeedback[];
	} = $props();

	const labels = $derived(Object.fromEntries(spec.items.map((item) => [item.id, item.label])));
</script>

<ol class="list">
	{#each answer.order as id, index (id)}
		<li class:ok={feedback[index]?.correct === true} class:bad={feedback[index]?.correct === false}>
			<span class="label">{labels[id]}</span>
			{#if feedback[index]}
				<span class="mark">{feedback[index].correct ? '✓ En su lugar' : '✗ Fuera de lugar'}</span>
			{/if}
			<span class="controls">
				<button
					type="button"
					aria-label={`Subir: ${labels[id]}`}
					disabled={index === 0}
					onclick={() => (answer.order = moveItem(answer.order, index, -1))}>↑</button
				>
				<button
					type="button"
					aria-label={`Bajar: ${labels[id]}`}
					disabled={index === answer.order.length - 1}
					onclick={() => (answer.order = moveItem(answer.order, index, 1))}>↓</button
				>
			</span>
		</li>
	{/each}
</ol>

<style>
	.list {
		margin: 0 0 14px;
		padding-left: 1.6rem;
	}

	li {
		display: flex;
		align-items: center;
		gap: 10px;
		padding: 8px 10px;
		margin-bottom: 6px;
		border: 1px solid var(--border);
		border-radius: 8px;
		background: var(--surface);
	}

	li.ok {
		border-color: var(--ok);
		background: #f2faf5;
	}

	li.bad {
		border-color: var(--danger);
		background: #fdf4f3;
	}

	.label {
		flex: 1;
	}

	.mark {
		font-size: 0.8rem;
		color: var(--muted);
	}

	.controls {
		display: flex;
		gap: 4px;
	}

	button {
		border: 1px solid var(--border);
		background: var(--bg);
		border-radius: 6px;
		width: 32px;
		height: 32px;
		cursor: pointer;
		font: inherit;
	}

	button:disabled {
		opacity: 0.4;
		cursor: default;
	}
</style>
