<script lang="ts">
	import { REQUIREMENT_STATE_LABEL, type RequirementState } from '../../../lib/api';
	import { formatDate } from '../../../lib/format';
	import StateBadge from '../../../lib/StateBadge.svelte';
	import type { PageProps } from './$types';

	let { data }: PageProps = $props();
	const c = $derived(data.completeness);
	const ORDER: RequirementState[] = ['in_force', 'draft', 'expired', 'unowned', 'missing'];
</script>

<p class="crumb"><a href="/documents">← Documentos</a></p>
<h1>Conjunto documental del PIMS</h1>
<p class="lead">
	Información documentada que la UNSA (ficticia) debe tener para su sistema de gestión de privacidad
	(ISO/IEC 27701): qué exige cada requisito, qué documento lo cubre y en qué estado está.
</p>

{#if c}
	<section class="card summary" aria-label="Resumen de completitud">
		<div>
			<p class="big" data-testid="completeness">
				{c.in_force} de {c.total} vigentes ({c.percent_in_force} %)
			</p>
			<progress value={c.in_force} max={c.total}></progress>
			<p class="meta">Estado a la fecha {formatDate(c.as_of + 'T00:00:00Z')}</p>
		</div>
		<ul class="counts" data-testid="state-counts">
			{#each ORDER as state (state)}
				<li><StateBadge {state} /> <strong>{c.counts[state]}</strong></li>
			{/each}
		</ul>
	</section>

	<div class="card table-card">
		<table data-testid="pims-table">
			<thead>
				<tr>
					<th>Cláusula*</th>
					<th>Requisito</th>
					<th>Estado</th>
					<th>Documento</th>
					<th>Responsable</th>
					<th>Revisión</th>
				</tr>
			</thead>
			<tbody>
				{#each c.items as item (item.code)}
					<tr data-testid={`pims-${item.code}`} data-state={item.state}>
						<td class="clause">{item.clause_ref}</td>
						<td>
							<strong>{item.title}</strong>
							<details>
								<summary>¿Qué se espera?</summary>
								<p>{item.summary}</p>
								<p><strong>Evidencia:</strong> {item.expected_evidence}</p>
							</details>
						</td>
						<td>
							<StateBadge state={item.state} />
							{#if item.issues.length > 1}
								<span class="issues">
									también: {item.issues
										.filter((i) => i !== item.state)
										.map((i) => REQUIREMENT_STATE_LABEL[i].toLowerCase())
										.join(', ')}
								</span>
							{/if}
						</td>
						<td>
							{#if item.document}
								<a href={`/documents/${item.document.code}`}>{item.document.title}</a>
								<span class="meta">v{item.document.current_version}</span>
							{:else}
								<span class="none">No existe</span>
							{/if}
						</td>
						<td>
							{item.document?.owner_unit_name ?? item.responsible_unit_name ?? '—'}
							{#if item.document && !item.document.owner_unit_code}
								<span class="meta">(sin asignar)</span>
							{:else if !item.document}
								<span class="meta">(sugerido)</span>
							{/if}
						</td>
						<td>
							{item.document?.review_date ? formatDate(item.document.review_date + 'T00:00:00Z') : '—'}
						</td>
					</tr>
				{/each}
			</tbody>
		</table>
	</div>

	<p class="footnote">
		* Las cláusulas se guardan como dato y deben verificarse contra la edición de la norma que use la
		universidad (la numeración difiere entre la edición 2019 y la 2025).
	</p>
{:else}
	<p class="card">No se pudo cargar la matriz. Verifica que el backend esté activo y ejecuta el seed.</p>
{/if}

<style>
	.crumb {
		margin: 0 0 8px;
	}

	.lead,
	.meta,
	.footnote {
		color: var(--muted);
	}

	.lead {
		max-width: 70ch;
	}

	.meta,
	.footnote {
		font-size: 0.85rem;
	}

	.summary {
		display: flex;
		gap: 32px;
		flex-wrap: wrap;
		align-items: center;
		margin: 16px 0;
	}

	.big {
		font-size: 1.3rem;
		font-weight: 700;
		margin: 0 0 6px;
	}

	progress {
		width: 260px;
		height: 10px;
	}

	.counts {
		list-style: none;
		margin: 0;
		padding: 0;
		display: flex;
		gap: 12px 20px;
		flex-wrap: wrap;
	}

	.table-card {
		padding: 0;
		overflow-x: auto;
	}

	table {
		width: 100%;
		border-collapse: collapse;
		font-size: 0.92rem;
	}

	th,
	td {
		text-align: left;
		padding: 10px 12px;
		border-bottom: 1px solid var(--border);
		vertical-align: top;
	}

	th {
		color: var(--muted);
		font-size: 0.8rem;
		font-weight: 600;
	}

	tr:last-child td {
		border-bottom: none;
	}

	.clause {
		white-space: nowrap;
		font-variant-numeric: tabular-nums;
	}

	details {
		margin-top: 4px;
		font-size: 0.88rem;
	}

	summary {
		cursor: pointer;
		color: var(--primary);
	}

	details p {
		margin: 6px 0;
		max-width: 60ch;
	}

	.issues {
		display: block;
		font-size: 0.75rem;
		color: var(--muted);
		margin-top: 2px;
	}

	.none {
		color: var(--danger);
	}
</style>
