<script lang="ts">
	import { CHANGE_STATUS_LABEL, type ChangeStatus } from './api';

	let { status }: { status: ChangeStatus } = $props();
</script>

<span class={`badge ${status}`} data-testid="change-status">{CHANGE_STATUS_LABEL[status]}</span>

<style>
	.badge {
		display: inline-block;
		border-radius: 999px;
		padding: 2px 10px;
		font-size: 0.78rem;
		border: 1px solid var(--border);
		background: var(--bg);
		color: var(--muted);
	}

	.open {
		color: var(--warn);
		border-color: #f0d1a5;
		background: #fff7ec;
	}

	.approved {
		color: var(--ok);
		border-color: #b4dcc2;
		background: #f2faf5;
	}

	.rejected {
		color: var(--danger);
		border-color: #efc2be;
		background: #fdf4f3;
	}
</style>
