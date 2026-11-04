<script lang="ts">
	import { IMPACT_HINT, IMPACT_LABEL, type ChangeImpact } from '../../../../lib/api';
	import type { PageProps } from './$types';

	let { data, form }: PageProps = $props();

	const impacts = Object.keys(IMPACT_LABEL) as ChangeImpact[];
</script>

<p class="crumb"><a href={`/documents/${data.doc.code}`}>← {data.doc.title}</a></p>
<h1>Proponer un cambio</h1>
<p class="lead">
	Edita el texto completo del documento (versión vigente v{data.doc.current_version}). El sistema
	calcula las diferencias y el superadmin decidirá si se aprueba.
</p>

<form method="POST" class="card form">
	{#if form?.error}<p class="error" role="alert" data-testid="form-error">{form.error}</p>{/if}

	<label>
		Título del cambio
		<input
			name="title"
			required
			maxlength="200"
			value={form?.values?.title ?? ''}
			placeholder="Ej.: Se corrige el plazo de entrega de actas"
		/>
	</label>

	<label>
		Justificación (¿por qué?)
		<textarea name="rationale" rows="3" required maxlength="5000"
			>{form?.values?.rationale ?? ''}</textarea
		>
	</label>

	<fieldset>
		<legend>Impacto del cambio</legend>
		{#each impacts as impact (impact)}
			<label class="radio">
				<input
					type="radio"
					name="impact"
					value={impact}
					required
					checked={(form?.values?.impact ?? '') === impact}
				/>
				<span><strong>{IMPACT_LABEL[impact]}</strong> — {IMPACT_HINT[impact]}</span>
			</label>
		{/each}
	</fieldset>

	<label>
		Texto propuesto (Markdown)
		<textarea
			name="proposed_content_md"
			rows="22"
			required
			class="mono"
			data-testid="proposed-content">{form?.values?.proposed_content_md ??
				data.doc.content_md}</textarea
		>
	</label>

	<div class="actions">
		<button type="submit">Enviar solicitud</button>
		<a href={`/documents/${data.doc.code}`}>Cancelar</a>
	</div>
</form>

<style>
	.crumb {
		margin: 0 0 8px;
	}

	.lead {
		color: var(--muted);
		max-width: 65ch;
	}

	.form {
		display: grid;
		gap: 16px;
	}

	label {
		display: grid;
		gap: 4px;
		font-size: 0.9rem;
	}

	input:not([type='radio']),
	textarea {
		padding: 9px 10px;
		border: 1px solid var(--border);
		border-radius: 8px;
		font: inherit;
	}

	.mono {
		font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
		font-size: 0.85rem;
	}

	fieldset {
		border: 1px solid var(--border);
		border-radius: 8px;
		padding: 10px 14px;
	}

	.radio {
		display: flex;
		gap: 8px;
		align-items: baseline;
		padding: 3px 0;
	}

	.actions {
		display: flex;
		gap: 16px;
		align-items: center;
	}

	button {
		background: var(--primary);
		color: var(--primary-contrast);
		border: none;
		border-radius: 8px;
		padding: 10px 16px;
		font: inherit;
		cursor: pointer;
	}

	.error {
		color: var(--danger);
		margin: 0;
	}
</style>
