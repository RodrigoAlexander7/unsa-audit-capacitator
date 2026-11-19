<script lang="ts">
	import ItemFeedbackNote from './ItemFeedbackNote.svelte';
	import type {
		ItemFeedback,
		NonconformityCaseAnswer,
		NonconformityFormAnswer,
		NonconformityFormSpec
	} from './types';

	let {
		spec,
		answer,
		feedback = []
	}: {
		spec: NonconformityFormSpec;
		answer: NonconformityFormAnswer;
		feedback?: ItemFeedback[];
	} = $props();

	const byId = $derived(Object.fromEntries(feedback.map((item) => [item.id, item])));

	function caseAns(id: string): NonconformityCaseAnswer {
		return (
			answer.cases[id] ?? {
				correction: '',
				root_cause: '',
				requires_action: null,
				action: '',
				responsible: '',
				implementation_date: '',
				verification_date: '',
				verification: '',
				doc_change: null,
				affected_document: ''
			}
		);
	}

	function patchCase(id: string, patch: Partial<NonconformityCaseAnswer>) {
		answer.cases[id] = { ...caseAns(id), ...patch };
	}
</script>

<div class="doc-scenario" data-testid="nc-scenario">
	<strong>Escenario.</strong>
	{spec.scenario}
	<p class="doc-help">
		Distingue entre corrección inmediata (contener el síntoma) y acción correctiva (eliminar la
		causa raíz), fija fechas coherentes y verifica eficacia después de implementar.
	</p>
</div>

{#each spec.cases as c (c.id)}
	{@const entry = caseAns(c.id)}
	{@const fb = byId[c.id]}
	<fieldset class="doc-card" class:ok={fb?.correct === true} class:bad={fb?.correct === false}>
		<legend>
			{c.title}
			<span class="doc-pill">Detectada: {c.detection_date}</span>
		</legend>

		<p class="doc-context">
			<strong>Hallazgo:</strong>
			{c.detection_context}
		</p>

		<div class="doc-field">
			<label for={`nc-corr-${c.id}`}>1. Corrección inmediata (contención)</label>
			<select
				id={`nc-corr-${c.id}`}
				aria-invalid={fb ? (fb.correct ? 'false' : 'true') : 'false'}
				value={entry.correction}
				onchange={(e) => patchCase(c.id, { correction: e.currentTarget.value })}
			>
				<option value="">Elige corrección…</option>
				{#each c.correction_options as opt (opt.id)}
					<option value={opt.id}>{opt.label}</option>
				{/each}
			</select>
		</div>

		<div class="doc-field">
			<label for={`nc-root-${c.id}`}>2. Análisis de causa raíz</label>
			<select
				id={`nc-root-${c.id}`}
				aria-invalid={fb ? (fb.correct ? 'false' : 'true') : 'false'}
				value={entry.root_cause}
				onchange={(e) => patchCase(c.id, { root_cause: e.currentTarget.value })}
			>
				<option value="">Elige causa raíz…</option>
				{#each c.root_cause_options as opt (opt.id)}
					<option value={opt.id}>{opt.label}</option>
				{/each}
			</select>
		</div>

		<div class="doc-field">
			<fieldset class="doc-multi">
				<legend class="doc-sublegend">3. ¿Requiere acción correctiva para evitar recurrencia?</legend>
				<div class="doc-radio-group">
					<label>
						<input
							type="radio"
							name={`nc-req-act-${c.id}`}
							checked={entry.requires_action === true}
							onchange={() => patchCase(c.id, { requires_action: true })}
						/>
						<span>Sí</span>
					</label>
					<label>
						<input
							type="radio"
							name={`nc-req-act-${c.id}`}
							checked={entry.requires_action === false}
							onchange={() => patchCase(c.id, { requires_action: false })}
						/>
						<span>No</span>
					</label>
				</div>
			</fieldset>
		</div>

		<div class="doc-field">
			<label for={`nc-act-${c.id}`}>4. Acción para eliminar la causa raíz</label>
			<select
				id={`nc-act-${c.id}`}
				aria-invalid={fb ? (fb.correct ? 'false' : 'true') : 'false'}
				value={entry.action}
				onchange={(e) => patchCase(c.id, { action: e.currentTarget.value })}
			>
				<option value="">Elige acción…</option>
				{#each c.action_options as opt (opt.id)}
					<option value={opt.id}>{opt.label}</option>
				{/each}
			</select>
		</div>

		<div class="doc-grid">
			<div class="doc-subgrid">
				<label for={`nc-resp-${c.id}`}>5. Responsable de ejecución</label>
				<select
					id={`nc-resp-${c.id}`}
					aria-invalid={fb ? (fb.correct ? 'false' : 'true') : 'false'}
					value={entry.responsible}
					onchange={(e) => patchCase(c.id, { responsible: e.currentTarget.value })}
				>
					<option value="">Elige cargo…</option>
					{#each spec.positions as pos (pos.id)}
						<option value={pos.id}>{pos.label}</option>
					{/each}
				</select>
			</div>

			<div class="doc-subgrid">
				<label for={`nc-imp-${c.id}`}>6. Fecha de implementación</label>
				<input
					id={`nc-imp-${c.id}`}
					type="date"
					aria-invalid={fb ? (fb.correct ? 'false' : 'true') : 'false'}
					value={entry.implementation_date}
					onchange={(e) => patchCase(c.id, { implementation_date: e.currentTarget.value })}
				/>
			</div>

			<div class="doc-subgrid">
				<label for={`nc-verd-${c.id}`}>7. Fecha de verificación de eficacia</label>
				<input
					id={`nc-verd-${c.id}`}
					type="date"
					aria-invalid={fb ? (fb.correct ? 'false' : 'true') : 'false'}
					value={entry.verification_date}
					onchange={(e) => patchCase(c.id, { verification_date: e.currentTarget.value })}
				/>
			</div>
		</div>

		<div class="doc-field">
			<label for={`nc-ver-${c.id}`}>8. Evidencia para verificar eficacia</label>
			<select
				id={`nc-ver-${c.id}`}
				aria-invalid={fb ? (fb.correct ? 'false' : 'true') : 'false'}
				value={entry.verification}
				onchange={(e) => patchCase(c.id, { verification: e.currentTarget.value })}
			>
				<option value="">Elige criterio de verificación…</option>
				{#each c.verification_options as opt (opt.id)}
					<option value={opt.id}>{opt.label}</option>
				{/each}
			</select>
		</div>

		<div class="doc-field">
			<fieldset class="doc-multi">
				<legend class="doc-sublegend">9. ¿Requiere actualizar algún documento del PIMS?</legend>
				<div class="doc-radio-group">
					<label>
						<input
							type="radio"
							name={`nc-doc-chg-${c.id}`}
							checked={entry.doc_change === true}
							onchange={() => patchCase(c.id, { doc_change: true })}
						/>
						<span>Sí</span>
					</label>
					<label>
						<input
							type="radio"
							name={`nc-doc-chg-${c.id}`}
							checked={entry.doc_change === false}
							onchange={() => patchCase(c.id, { doc_change: false, affected_document: '' })}
						/>
						<span>No</span>
					</label>
				</div>
			</fieldset>
		</div>

		<div class="doc-field">
			<label for={`nc-doc-${c.id}`}>10. Documento del PIMS a actualizar</label>
			<select
				id={`nc-doc-${c.id}`}
				disabled={entry.doc_change !== true}
				aria-invalid={fb ? (fb.correct ? 'false' : 'true') : 'false'}
				value={entry.affected_document}
				onchange={(e) => patchCase(c.id, { affected_document: e.currentTarget.value })}
			>
				<option value="">
					{entry.doc_change === true ? 'Elige documento afectado…' : 'Sin cambio documental'}
				</option>
				{#each spec.documents as doc (doc.id)}
					<option value={doc.id}>{doc.label}</option>
				{/each}
			</select>
		</div>

		<ItemFeedbackNote feedback={fb} id={`fb-${c.id}`} />
	</fieldset>
{/each}
