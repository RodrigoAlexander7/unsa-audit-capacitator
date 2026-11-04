<script lang="ts">
	import { ROUTE_STATUS_LABEL, type RouteStatus } from './api';

	let { status }: { status: RouteStatus } = $props();
</script>

<span class={`badge ${status}`} data-testid="route-status">{ROUTE_STATUS_LABEL[status]}</span>

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

	.available {
		color: var(--primary);
		border-color: #b8cdea;
		background: #eef3fb;
	}

	.in_progress {
		color: var(--warn);
		border-color: #f0d1a5;
		background: #fff7ec;
	}

	.completed {
		color: var(--ok);
		border-color: #b4dcc2;
		background: #f2faf5;
	}
</style>
