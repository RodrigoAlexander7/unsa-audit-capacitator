<script lang="ts">
	import { KIND_LABEL } from '../../../lib/api';
	import type { PageProps } from './$types';

	let { data }: PageProps = $props();
	const d = $derived(data.detail);
</script>

<p class="crumb"><a href="/university">← Organigrama</a></p>
<h1>{d.unit.name}</h1>
<p class="lead">
	{KIND_LABEL[d.unit.kind] ?? d.unit.kind} · código {d.unit.code}
	{#if d.parent}· depende de <a href={`/university/${d.parent.id}`}>{d.parent.name}</a>{/if}
</p>

<section class="card">
	<h2>Cargos</h2>
	{#if d.positions.length}
		<table>
			<thead>
				<tr><th>Cargo</th><th>Titular</th><th>Reporta a</th></tr>
			</thead>
			<tbody>
				{#each d.positions as p (p.id)}
					<tr>
						<td>{p.title}</td>
						<td>{p.holder?.full_name ?? '—'}</td>
						<td>{p.reports_to_title ?? '—'}</td>
					</tr>
				{/each}
			</tbody>
		</table>
	{:else}
		<p class="muted">Esta unidad no tiene cargos registrados.</p>
	{/if}
</section>

{#if d.children.length}
	<section class="card">
		<h2>Unidades dependientes</h2>
		<ul>
			{#each d.children as c (c.id)}
				<li><a href={`/university/${c.id}`}>{c.name}</a> <span class="muted">({KIND_LABEL[c.kind] ?? c.kind})</span></li>
			{/each}
		</ul>
	</section>
{/if}

<style>
	.crumb {
		margin: 0 0 8px;
	}

	.lead,
	.muted {
		color: var(--muted);
	}

	.card {
		margin-top: 16px;
	}

	table {
		width: 100%;
		border-collapse: collapse;
		font-size: 0.95rem;
	}

	th,
	td {
		text-align: left;
		padding: 8px 10px;
		border-bottom: 1px solid var(--border);
	}

	th {
		color: var(--muted);
		font-weight: 600;
		font-size: 0.8rem;
	}
</style>
