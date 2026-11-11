<script lang="ts">
	import { IMPACT_HINT, IMPACT_LABEL } from '../../../../../lib/api';
	import ChangeBadge from '../../../../../lib/ChangeBadge.svelte';
	import DiffView from '../../../../../lib/DiffView.svelte';
	import { formatDate } from '../../../../../lib/format';
	import type { PageProps } from './$types';

	let { data, form }: PageProps = $props();
	const change = $derived(data.change);
	const isAdmin = $derived(data.user?.role === 'superadmin');
</script>

<p class="crumb"><a href={`/documents/${change.document_code}`}>← {change.document_code}</a></p>
<h1>{change.title} <ChangeBadge status={change.status} /></h1>

<dl class="facts card">
	<div><dt>Documento</dt><dd>{change.document_code} (base v{change.base_version})</dd></div>
	<div>
		<dt>Impacto</dt>
		<dd>{IMPACT_LABEL[change.impact]} — {IMPACT_HINT[change.impact]}</dd>
	</div>
	<div>
		<dt>Propuesta por</dt>
		<dd>{change.proposed_by_name}, {formatDate(change.created_at)}</dd>
	</div>
	{#if change.resolved_at}
		<div>
			<dt>Resuelta por</dt>
			<dd>
				{change.resolved_by_name}, {formatDate(change.resolved_at)}
				{#if change.resolution_note}— «{change.resolution_note}»{/if}
			</dd>
		</div>
	{/if}
	{#if change.resulting_version}
		<div>
			<dt>Resultado</dt>
			<dd>
				Creó la versión v{change.resulting_version} —
				<a
					href={`/documents/${change.document_code}/diff?from=${change.base_version}&to=${change.resulting_version}`}
					>ver diferencias</a
				>
			</dd>
		</div>
	{/if}
</dl>

<section class="card">
	<h2>Justificación</h2>
	<p class="rationale">{change.rationale}</p>
</section>

<section class="card">
	<h2>Cambios propuestos</h2>
	<DiffView diff={change.diff} />
</section>

{#if change.status === 'open'}
	{#if isAdmin}
		<form method="POST" class="card resolve" data-testid="resolve-form">
			<h2>Resolver</h2>
			{#if form?.error}<p class="error" role="alert" data-testid="form-error">{form.error}</p>{/if}
			<label>
				Nota (opcional)
				<textarea name="note" rows="2" maxlength="2000">{form?.note ?? ''}</textarea>
			</label>
			<div class="actions">
				<button type="submit" formaction="?/approve" class="approve">Aprobar y crear versión</button>
				<button type="submit" formaction="?/reject" class="reject">Rechazar</button>
			</div>
		</form>
	{:else}
		<p class="card muted">Esta solicitud espera la decisión del superadmin.</p>
	{/if}
{/if}

<style>
	.crumb {
		margin: 0 0 8px;
	}

	h1 {
		display: flex;
		flex-wrap: wrap;
		gap: 12px;
		align-items: center;
	}

	.card {
		margin: 16px 0;
	}

	h2 {
		margin-top: 0;
		font-size: 1.1rem;
	}

	.facts {
		display: grid;
		gap: 8px;
		margin: 0;
	}

	.facts div {
		display: grid;
		grid-template-columns: 9rem 1fr;
		gap: 10px;
	}

	dt {
		color: var(--muted);
		font-size: 0.85rem;
	}

	dd {
		margin: 0;
	}

	.rationale {
		white-space: pre-wrap;
		margin: 0;
	}

	.muted {
		color: var(--muted);
	}

	label {
		display: grid;
		gap: 4px;
		font-size: 0.9rem;
	}

	textarea {
		padding: 9px 10px;
		border: 1px solid var(--border);
		border-radius: 8px;
		font: inherit;
	}

	.actions {
		display: flex;
		gap: 12px;
		margin-top: 12px;
	}

	button {
		border: none;
		border-radius: 8px;
		padding: 10px 16px;
		font: inherit;
		cursor: pointer;
		color: #fff;
	}

	.approve {
		background: var(--ok);
	}

	.reject {
		background: var(--danger);
	}

	.error {
		color: var(--danger);
	}
</style>
