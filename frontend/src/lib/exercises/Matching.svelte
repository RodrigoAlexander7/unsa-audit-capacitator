<script lang="ts">
	import type { ItemFeedback, MatchingSpec } from './types';

	let {
		spec,
		answer,
		feedback = []
	}: {
		spec: MatchingSpec;
		answer: { assignments: Record<string, string> };
		feedback?: ItemFeedback[];
	} = $props();

	const byId = $derived(Object.fromEntries(feedback.map((item) => [item.id, item])));
</script>

<ul class="rows">
	{#each spec.left as item (item.id)}
		{@const fb = byId[item.id]}
		<li class:ok={fb?.correct === true} class:bad={fb?.correct === false}>
			<label for={`m-${item.id}`}>{item.label}</label>
			<select
				id={`m-${item.id}`}
				value={answer.assignments[item.id] ?? ''}
				onchange={(event) => (answer.assignments[item.id] = event.currentTarget.value)}
			>
				<option value="">Elige…</option>
				{#each spec.right as option (option.id)}
					<option value={option.id}>{option.label}</option>
				{/each}
			</select>
			{#if fb}<span class="mark">{fb.correct ? '✓' : '✗'}</span>{/if}
		</li>
	{/each}
</ul>

<style>
	.rows {
		list-style: none;
		margin: 0 0 14px;
		padding: 0;
	}

	li {
		display: grid;
		grid-template-columns: 1fr minmax(160px, 1fr) 24px;
		gap: 10px;
		align-items: center;
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

	select {
		padding: 7px 8px;
		border: 1px solid var(--border);
		border-radius: 6px;
		font: inherit;
		background: #fff;
	}

	.mark {
		font-weight: 700;
	}

	@media (max-width: 560px) {
		li {
			grid-template-columns: 1fr 24px;
		}

		label {
			grid-column: 1 / -1;
		}
	}
</style>
