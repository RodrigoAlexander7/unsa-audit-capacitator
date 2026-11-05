<script lang="ts">
	import ItemFeedbackNote from './ItemFeedbackNote.svelte';
	import type {
		ItemFeedback,
		TreatmentRowAnswer,
		TreatmentTableAnswer,
		TreatmentTableSpec
	} from './types';

	let {
		spec,
		answer,
		feedback = []
	}: {
		spec: TreatmentTableSpec;
		answer: TreatmentTableAnswer;
		feedback?: ItemFeedback[];
	} = $props();

	const byId = $derived(Object.fromEntries(feedback.map((item) => [item.id, item])));
	const scaleOpts = [
		{ value: '0', label: '0 — Baja' },
		{ value: '1', label: '1 — Media' },
		{ value: '2', label: '2 — Alta' }
	];

	function rowAns(id: string): TreatmentRowAnswer {
		return (
			answer.rows[id] ?? {
				option: '',
				control_id: '',
				owner: '',
				deadline: '',
				residual_consequence: null,
				residual_probability: null
			}
		);
	}

	function patchRow(id: string, patch: Partial<TreatmentRowAnswer>) {
		answer.rows[id] = { ...rowAns(id), ...patch };
	}

	function onOptionChange(id: string, option: string) {
		const clearCtrl = option === 'accept' || option === 'avoid';
		patchRow(id, { option, ...(clearCtrl ? { control_id: '' } : {}) });
	}
</script>

<div class="doc-scenario" data-testid="treatment-scenario">
	<strong>Escenario.</strong>
	{spec.scenario}
	<p class="doc-help">
		Elige la opción de tratamiento, verifica que el control figure como aplicable en la SoA cuando
		corresponda, asigna responsable competente, plazo real y estima el riesgo residual (C + P).
	</p>
</div>

{#each spec.rows as row (row.id)}
	{@const entry = rowAns(row.id)}
	{@const fb = byId[row.id]}
	{@const noCtrlNeeded = entry.option === 'accept' || entry.option === 'avoid'}
	{@const resLevel =
		entry.residual_consequence !== null && entry.residual_probability !== null
			? entry.residual_consequence + entry.residual_probability
			: null}
	<fieldset class="doc-card" class:ok={fb?.correct === true} class:bad={fb?.correct === false}>
		<legend>
			{row.asset}
			<span class="doc-pill"
				>Inicial: C={row.initial_consequence}, P={row.initial_probability} → {row.initial_risk}</span
			>
		</legend>

		<div class="doc-meta-strip">
			<span><strong>Amenaza:</strong> {row.threat}</span>
			<span><strong>Vulnerabilidad:</strong> {row.vulnerability}</span>
			<span><strong>Dueño del riesgo:</strong> {row.risk_owner}</span>
		</div>

		<div class="doc-grid">
			<div class="doc-subgrid">
				<label for={`tt-opt-${row.id}`}>Opción de tratamiento</label>
				<select
					id={`tt-opt-${row.id}`}
					aria-invalid={fb ? (fb.correct ? 'false' : 'true') : 'false'}
					value={entry.option}
					onchange={(e) => onOptionChange(row.id, e.currentTarget.value)}
				>
					<option value="">Elige opción…</option>
					{#each spec.options as opt (opt.id)}
						<option value={opt.id}>{opt.label}</option>
					{/each}
				</select>
			</div>

			<div class="doc-subgrid">
				<label for={`tt-ctrl-${row.id}`}>Control de la SoA</label>
				<select
					id={`tt-ctrl-${row.id}`}
					disabled={noCtrlNeeded}
					aria-invalid={fb ? (fb.correct ? 'false' : 'true') : 'false'}
					value={entry.control_id}
					onchange={(e) => patchRow(row.id, { control_id: e.currentTarget.value })}
				>
					<option value="">
						{noCtrlNeeded ? 'No aplica a esta opción' : 'Elige control de la SoA…'}
					</option>
					{#each spec.soa_controls as ctrl (ctrl.id)}
						<option value={ctrl.id}>{ctrl.label}</option>
					{/each}
				</select>
			</div>

			<div class="doc-subgrid">
				<label for={`tt-own-${row.id}`}>Responsable de ejecución</label>
				<select
					id={`tt-own-${row.id}`}
					aria-invalid={fb ? (fb.correct ? 'false' : 'true') : 'false'}
					value={entry.owner}
					onchange={(e) => patchRow(row.id, { owner: e.currentTarget.value })}
				>
					<option value="">Elige responsable…</option>
					{#each spec.owners as owner (owner.id)}
						<option value={owner.id}>{owner.label}</option>
					{/each}
				</select>
			</div>

			<div class="doc-subgrid">
				<label for={`tt-dl-${row.id}`}>Plazo de implementación</label>
				<input
					id={`tt-dl-${row.id}`}
					type="date"
					aria-invalid={fb ? (fb.correct ? 'false' : 'true') : 'false'}
					value={entry.deadline}
					onchange={(e) => patchRow(row.id, { deadline: e.currentTarget.value })}
				/>
			</div>

			<div class="doc-subgrid">
				<label for={`tt-rc-${row.id}`}>Consecuencia residual (0–2)</label>
				<select
					id={`tt-rc-${row.id}`}
					aria-invalid={fb ? (fb.correct ? 'false' : 'true') : 'false'}
					value={entry.residual_consequence === null ? '' : String(entry.residual_consequence)}
					onchange={(e) =>
						patchRow(row.id, {
							residual_consequence:
								e.currentTarget.value === '' ? null : Number(e.currentTarget.value)
						})}
				>
					<option value="">Elige…</option>
					{#each scaleOpts as opt (opt.value)}
						<option value={opt.value}>{opt.label}</option>
					{/each}
				</select>
			</div>

			<div class="doc-subgrid">
				<label for={`tt-rp-${row.id}`}>Probabilidad residual (0–2)</label>
				<select
					id={`tt-rp-${row.id}`}
					aria-invalid={fb ? (fb.correct ? 'false' : 'true') : 'false'}
					value={entry.residual_probability === null ? '' : String(entry.residual_probability)}
					onchange={(e) =>
						patchRow(row.id, {
							residual_probability:
								e.currentTarget.value === '' ? null : Number(e.currentTarget.value)
						})}
				>
					<option value="">Elige…</option>
					{#each scaleOpts as opt (opt.value)}
						<option value={opt.value}>{opt.label}</option>
					{/each}
				</select>
			</div>
		</div>

		{#if resLevel !== null}
			<p class="doc-risk-readout" class:low={resLevel < row.initial_risk} class:high={resLevel > row.initial_risk}>
				<strong>Riesgo residual calculado: {resLevel} / 4</strong> (inicial: {row.initial_risk})
			</p>
		{/if}

		<ItemFeedbackNote feedback={fb} id={`fb-${row.id}`} />
	</fieldset>
{/each}
