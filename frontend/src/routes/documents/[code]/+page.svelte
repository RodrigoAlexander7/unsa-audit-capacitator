<script lang="ts">
	import { DOCUMENT_KIND_LABEL, IMPACT_LABEL } from '../../../lib/api';
	import ChangeBadge from '../../../lib/ChangeBadge.svelte';
	import { formatDate } from '../../../lib/format';
	import type { PageProps } from './$types';

	let { data }: PageProps = $props();
	const doc = $derived(data.doc);
</script>

<p class="crumb"><a href="/documents">← Documentos</a></p>
<h1>{doc.title}</h1>
<p class="meta">
	{DOCUMENT_KIND_LABEL[doc.kind] ?? doc.kind} · responsable: {doc.owner_unit_name ?? '—'} ·
	<strong data-testid="current-version">versión vigente v{doc.current_version}</strong>
	({formatDate(doc.updated_at)})
	{#if doc.lifecycle === 'draft'}· <strong class="draft">Borrador</strong>{/if}
	{#if doc.review_date}· revisión: {formatDate(doc.review_date + 'T00:00:00Z')}{/if}
</p>

<div class="actions">
	{#if doc.current_version > 1}
		<a class="button secondary" href={`/documents/${doc.code}/diff?to=${doc.current_version}`}
			>Ver diferencias con la versión anterior</a
		>
	{/if}
	<a class="button" href={`/documents/${doc.code}/propose`}>Proponer un cambio</a>
</div>

<article class="card content" data-testid="document-content">
	<!-- eslint-disable-next-line svelte/no-at-html-tags -- contenido institucional aprobado -->
	{@html data.html}
</article>

<section class="card">
	<h2>Historial de versiones</h2>
	<table data-testid="versions-table">
		<thead>
			<tr><th>Versión</th><th>Fecha</th><th>Autor</th><th>Mensaje</th><th></th></tr>
		</thead>
		<tbody>
			{#each data.versions as version (version.number)}
				<tr>
					<td>v{version.number}</td>
					<td>{formatDate(version.created_at)}</td>
					<td>{version.author_label}</td>
					<td>{version.message}</td>
					<td class="links">
						{#if version.parent_number}
							<a href={`/documents/${doc.code}/diff?from=${version.parent_number}&to=${version.number}`}
								>diff</a
							>
						{/if}
					</td>
				</tr>
			{/each}
		</tbody>
	</table>
</section>

<section class="card">
	<h2>Solicitudes de cambio</h2>
	{#if data.requests.length}
		<ul class="requests" data-testid="document-requests">
			{#each data.requests as request (request.id)}
				<li>
					<a href={`/documents/${doc.code}/changes/${request.id}`}>{request.title}</a>
					<ChangeBadge status={request.status} />
					<span class="meta">
						impacto {IMPACT_LABEL[request.impact].toLowerCase()} · {request.proposed_by_name} ·
						{formatDate(request.created_at)}
						{#if request.resulting_version}· dio origen a v{request.resulting_version}{/if}
					</span>
				</li>
			{/each}
		</ul>
	{:else}
		<p class="meta">Aún no hay solicitudes para este documento.</p>
	{/if}
</section>

<style>
	.crumb {
		margin: 0 0 8px;
	}

	.meta {
		color: var(--muted);
		font-size: 0.9rem;
	}

	.draft {
		color: var(--primary);
	}

	.actions {
		display: flex;
		gap: 10px;
		flex-wrap: wrap;
		margin: 14px 0;
	}

	.button {
		background: var(--primary);
		color: var(--primary-contrast);
		text-decoration: none;
		padding: 8px 14px;
		border-radius: 8px;
	}

	.button.secondary {
		background: var(--surface);
		color: var(--primary);
		border: 1px solid var(--border);
	}

	.card {
		margin: 16px 0;
	}

	.content :global(h1) {
		font-size: 1.4rem;
		margin-top: 0;
	}

	.content :global(table) {
		border-collapse: collapse;
		width: 100%;
		margin: 12px 0;
		font-size: 0.92rem;
	}

	.content :global(th),
	.content :global(td) {
		border: 1px solid var(--border);
		padding: 6px 10px;
		text-align: left;
	}

	.content :global(blockquote) {
		margin: 12px 0;
		padding: 4px 14px;
		border-left: 3px solid var(--border);
		color: var(--muted);
	}

	table {
		width: 100%;
		border-collapse: collapse;
		font-size: 0.92rem;
	}

	section th,
	section td {
		text-align: left;
		padding: 8px 10px;
		border-bottom: 1px solid var(--border);
	}

	h2 {
		margin-top: 0;
		font-size: 1.1rem;
	}

	.requests {
		list-style: none;
		padding: 0;
		margin: 0;
		display: grid;
		gap: 10px;
	}

	.requests .meta {
		display: block;
	}
</style>
