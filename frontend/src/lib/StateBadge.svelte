<script lang="ts">
	import { REQUIREMENT_STATE_LABEL, type RequirementState } from './api';

	let { state }: { state: RequirementState } = $props();
</script>

<span class={`badge ${state}`} data-testid="requirement-state" data-state={state}>
	<span aria-hidden="true">{state === 'in_force' ? '✓' : state === 'missing' ? '✗' : '!'}</span>
	{REQUIREMENT_STATE_LABEL[state]}
</span>

<style>
	.badge {
		display: inline-flex;
		gap: 4px;
		align-items: center;
		border-radius: 999px;
		padding: 2px 10px;
		font-size: 0.78rem;
		border: 1px solid var(--border);
		background: var(--bg);
		color: var(--muted);
		white-space: nowrap;
	}

	.in_force {
		color: var(--ok);
		border-color: #b4dcc2;
		background: #f2faf5;
	}

	.draft {
		color: var(--primary);
		border-color: #b8cdea;
		background: #eef3fb;
	}

	.expired,
	.unowned {
		color: var(--warn);
		border-color: #f0d1a5;
		background: #fff7ec;
	}

	.missing {
		color: var(--danger);
		border-color: #efc2be;
		background: #fdf4f3;
	}
</style>
