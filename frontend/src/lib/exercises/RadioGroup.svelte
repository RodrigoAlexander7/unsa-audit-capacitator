<script lang="ts">
	import DiffText from '../DiffText.svelte';
	import type { ItemFeedback, Opt } from './types';

	let {
		name,
		legend,
		options,
		value,
		onselect,
		feedback = undefined
	}: {
		name: string;
		legend: string;
		options: Opt[];
		value: string | undefined;
		onselect: (id: string) => void;
		feedback?: ItemFeedback | undefined;
	} = $props();
</script>

<fieldset class:ok={feedback?.correct === true} class:bad={feedback?.correct === false}>
	<legend><DiffText text={legend} /></legend>
	{#each options as option (option.id)}
		<label class="option">
			<input
				type="radio"
				{name}
				value={option.id}
				checked={value === option.id}
				onchange={() => onselect(option.id)}
			/>
			<span>{option.label}</span>
		</label>
	{/each}
	{#if feedback}
		<p class="feedback" role="status">
			<strong>{feedback.correct ? '✓ Correcto' : '✗ Incorrecto'}</strong>
			{#if feedback.feedback}— {feedback.feedback}{/if}
		</p>
	{/if}
</fieldset>

<style>
	fieldset {
		border: 1px solid var(--border);
		border-radius: 8px;
		padding: 12px 14px;
		margin: 0 0 14px;
	}

	fieldset.ok {
		border-color: var(--ok);
		background: #f2faf5;
	}

	fieldset.bad {
		border-color: var(--danger);
		background: #fdf4f3;
	}

	legend {
		font-weight: 600;
		padding: 0 6px;
		white-space: pre-wrap;
		max-width: 100%;
	}

	.option {
		display: flex;
		gap: 8px;
		align-items: flex-start;
		padding: 4px 0;
		cursor: pointer;
	}

	.feedback {
		margin: 8px 0 0;
		font-size: 0.9rem;
	}
</style>
