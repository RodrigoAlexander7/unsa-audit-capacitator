<script lang="ts">
	import { DOCUMENT_KIND_LABEL, IMPACT_LABEL, LIFECYCLE_LABEL } from '../../lib/api';
	import ChangeBadge from '../../lib/ChangeBadge.svelte';
	import { formatDate } from '../../lib/format';
	import type { PageProps } from './$types';

	let { data }: PageProps = $props();
</script>

<h1>Documentos institucionales</h1>
<p class="lead">
	Normas internas de la UNSA (ficticia) con su historial de versiones. Cada cambio queda registrado:
	qué cambió, quién, cuándo y por qué.
</p>
<p><a class="pims-link" href="/documents/pims">Ver el conjunto documental del PIMS (privacidad) →</a></p>

<div class="card table-card">
	<table data-testid="documents-table">
		<thead>
			<tr>
				<th>Documento</th>
				<th>Tipo</th>
				<th>Responsable</th>
				<th>Estado</th>
				<th>Versión</th>
				<th>Actualizado</th>
				<th>Solicitudes</th>
			</tr>
		</thead>
		<tbody>
			{#each data.documents as doc (doc.code)}
				<tr>
					<td><a href={`/documents/${doc.code}`}>{doc.title}</a></td>
					<td>{DOCUMENT_KIND_LABEL[doc.kind] ?? doc.kind}</td>
					<td>{doc.owner_unit_name ?? '—'}</td>
					<td data-testid={`lifecycle-${doc.code}`}>{LIFECYCLE_LABEL[doc.lifecycle] ?? doc.lifecycle}</td>
					<td>v{doc.current_version}</td>
					<td>{formatDate(doc.updated_at)}</td>
					<td>{doc.open_change_requests > 0 ? `${doc.open_change_requests} abierta(s)` : '—'}</td>
				</tr>
			{:else}
				<tr><td colspan="7">No hay documentos cargados. Ejecuta el seed del backend.</td></tr>
			{/each}
		</tbody>
	</table>
</div>

<h2>Solicitudes de cambio abiertas</h2>
{#if data.openRequests.length}
	<ul class="requests" data-testid="open-requests">
		{#each data.openRequests as request (request.id)}
			<li class="card">
				<div class="head">
					<a href={`/documents/${request.document_code}/changes/${request.id}`}>{request.title}</a>
					<ChangeBadge status={request.status} />
				</div>
				<p class="meta">
					{request.document_code} · base v{request.base_version} · impacto {IMPACT_LABEL[
						request.impact
					].toLowerCase()} · {request.proposed_by_name} · {formatDate(request.created_at)}
				</p>
			</li>
		{/each}
	</ul>
{:else}
	<p class="muted">No hay solicitudes abiertas.</p>
{/if}

<style>
	.lead,
	.muted {
		color: var(--muted);
		max-width: 65ch;
	}

	.table-card {
		padding: 0;
		overflow-x: auto;
	}

	table {
		width: 100%;
		border-collapse: collapse;
		font-size: 0.95rem;
	}

	th,
	td {
		text-align: left;
		padding: 10px 14px;
		border-bottom: 1px solid var(--border);
	}

	th {
		color: var(--muted);
		font-size: 0.8rem;
		font-weight: 600;
	}

	tr:last-child td {
		border-bottom: none;
	}

	h2 {
		margin-top: 28px;
	}

	.requests {
		list-style: none;
		padding: 0;
		margin: 0;
		display: grid;
		gap: 10px;
	}

	.head {
		display: flex;
		justify-content: space-between;
		gap: 12px;
		align-items: center;
	}

	.meta {
		margin: 6px 0 0;
		color: var(--muted);
		font-size: 0.85rem;
	}
</style>
