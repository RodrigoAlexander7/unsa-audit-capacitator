<script lang="ts">
	import type { DiffResult } from './api';

	let { diff }: { diff: DiffResult } = $props();

	const SIGN = { add: '+', del: '−', ctx: ' ' } as const;
	const LABEL = { add: 'Añadido', del: 'Eliminado', ctx: 'Sin cambios' } as const;
</script>

<p class="stats" data-testid="diff-stats">
	<span class="plus">+{diff.additions}</span> añadidas · <span class="minus">−{diff.deletions}</span> eliminadas
</p>

{#if diff.hunks.length === 0}
	<p class="empty">No hay diferencias entre estas versiones.</p>
{/if}

{#each diff.hunks as hunk, index (index)}
	<div class="hunk" role="group" aria-label={`Cambio ${index + 1}`}>
		<div class="hunk-head">@@ −{hunk.old_start} +{hunk.new_start} @@</div>
		<table>
			<tbody>
				{#each hunk.lines as line, i (i)}
					<tr class={line.kind} data-testid={`diff-${line.kind}`}>
						<td class="no">{line.old_line ?? ''}</td>
						<td class="no">{line.new_line ?? ''}</td>
						<td class="sign" aria-label={LABEL[line.kind]}>{SIGN[line.kind]}</td>
						<td class="text">{line.text}</td>
					</tr>
				{/each}
			</tbody>
		</table>
	</div>
{/each}

<style>
	.stats {
		margin: 0 0 10px;
		color: var(--muted);
	}

	.plus {
		color: var(--ok);
		font-weight: 600;
	}

	.minus {
		color: var(--danger);
		font-weight: 600;
	}

	.hunk {
		border: 1px solid var(--border);
		border-radius: 8px;
		overflow: hidden;
		margin-bottom: 14px;
		background: var(--surface);
	}

	.hunk-head {
		background: var(--bg);
		color: var(--muted);
		font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
		font-size: 0.8rem;
		padding: 4px 10px;
		border-bottom: 1px solid var(--border);
	}

	table {
		border-collapse: collapse;
		width: 100%;
		font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
		font-size: 0.85rem;
	}

	td {
		padding: 1px 6px;
		vertical-align: top;
	}

	.no {
		width: 3rem;
		text-align: right;
		color: var(--muted);
		user-select: none;
		border-right: 1px solid var(--border);
	}

	.sign {
		width: 1.5rem;
		text-align: center;
		font-weight: 700;
	}

	.text {
		white-space: pre-wrap;
		word-break: break-word;
	}

	tr.add {
		background: #e9f7ee;
	}

	tr.add .sign {
		color: var(--ok);
	}

	tr.del {
		background: #fdeceb;
	}

	tr.del .sign {
		color: var(--danger);
	}

	.empty {
		color: var(--muted);
	}
</style>
