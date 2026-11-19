<script lang="ts">
	import ItemFeedbackNote from './ItemFeedbackNote.svelte';
	import { computeRiskStatus } from './logic';
	import type { ItemFeedback, RiskRowAnswer, RiskTableAnswer, RiskTableSpec } from './types';

	let {
		spec,
		answer,
		feedback = []
	}: {
		spec: RiskTableSpec;
		answer: RiskTableAnswer;
		feedback?: ItemFeedback[];
	} = $props();

	const byId = $derived(Object.fromEntries(feedback.map((item) => [item.id, item])));
	const scaleOpts = [
		{ value: '0', label: '0 — Baja' },
		{ value: '1', label: '1 — Media' },
		{ value: '2', label: '2 — Alta' }
	];

	function rowAns(id: string): RiskRowAnswer {
		return answer.rows[id] ?? { consequence: null, probability: null };
	}

	function patchRow(id: string, patch: Partial<RiskRowAnswer>) {
		answer.rows[id] = { ...rowAns(id), ...patch };
	}
</script>

<div class="doc-scenario" data-testid="risk-scenario">
	<strong>Escenario.</strong>
	{spec.scenario}
	<p class="doc-help">
		Escala UNSA: 0 = Baja, 1 = Media, 2 = Alta · Riesgo = Consecuencia + Probabilidad · Umbral de
		aceptación: &lt; {spec.threshold} (≥ {spec.threshold} requiere tratamiento).
	</p>
</div>

{#each spec.rows as row (row.id)}
	{@const entry = rowAns(row.id)}
	{@const fb = byId[row.id]}
	{@const status = computeRiskStatus(entry.consequence, entry.probability, spec.threshold)}
	<fieldset class="doc-card" class:ok={fb?.correct === true} class:bad={fb?.correct === false}>
		<legend>{row.asset}</legend>

		<div class="doc-meta-strip">
			<span><strong>Dueño del activo:</strong> {row.asset_owner}</span>
			<span>
				<strong>Datos tratados:</strong>
				{row.data_categories.length ? row.data_categories.join(', ') : 'Sin datos personales'}
			</span>
			<span><strong>Controles existentes:</strong> {row.existing_controls || 'Ninguno'}</span>
		</div>

		<div class="doc-grid">
			<div class="doc-subgrid">
				{#if row.threat_options}
					<label for={`rt-thr-${row.id}`}>Amenaza probable</label>
					<select
						id={`rt-thr-${row.id}`}
						aria-invalid={fb ? (fb.correct ? 'false' : 'true') : 'false'}
						value={entry.threat ?? ''}
						onchange={(e) => patchRow(row.id, { threat: e.currentTarget.value })}
					>
						<option value="">Elige amenaza…</option>
						{#each row.threat_options as opt (opt.id)}
							<option value={opt.id}>{opt.label}</option>
						{/each}
					</select>
				{:else}
					<div class="doc-readonly">
						<span class="doc-ro-label">Amenaza</span>
						<span>{row.threat}</span>
					</div>
				{/if}
			</div>

			<div class="doc-subgrid">
				{#if row.vulnerability_options}
					<label for={`rt-vul-${row.id}`}>Vulnerabilidad observada</label>
					<select
						id={`rt-vul-${row.id}`}
						aria-invalid={fb ? (fb.correct ? 'false' : 'true') : 'false'}
						value={entry.vulnerability ?? ''}
						onchange={(e) => patchRow(row.id, { vulnerability: e.currentTarget.value })}
					>
						<option value="">Elige vulnerabilidad…</option>
						{#each row.vulnerability_options as opt (opt.id)}
							<option value={opt.id}>{opt.label}</option>
						{/each}
					</select>
				{:else}
					<div class="doc-readonly">
						<span class="doc-ro-label">Vulnerabilidad</span>
						<span>{row.vulnerability}</span>
					</div>
				{/if}
			</div>

			<div class="doc-subgrid">
				{#if row.risk_owner_options}
					<label for={`rt-own-${row.id}`}>Propietario del riesgo</label>
					<select
						id={`rt-own-${row.id}`}
						aria-invalid={fb ? (fb.correct ? 'false' : 'true') : 'false'}
						value={entry.risk_owner ?? ''}
						onchange={(e) => patchRow(row.id, { risk_owner: e.currentTarget.value })}
					>
						<option value="">Elige propietario…</option>
						{#each row.risk_owner_options as opt (opt.id)}
							<option value={opt.id}>{opt.label}</option>
						{/each}
					</select>
				{:else}
					<div class="doc-readonly">
						<span class="doc-ro-label">Propietario del riesgo</span>
						<span>{row.risk_owner}</span>
					</div>
				{/if}
			</div>

			<div class="doc-subgrid">
				<label for={`rt-c-${row.id}`}>Consecuencia (0–2)</label>
				<select
					id={`rt-c-${row.id}`}
					aria-invalid={fb ? (fb.correct ? 'false' : 'true') : 'false'}
					value={entry.consequence === null ? '' : String(entry.consequence)}
					onchange={(e) =>
						patchRow(row.id, {
							consequence: e.currentTarget.value === '' ? null : Number(e.currentTarget.value)
						})}
				>
					<option value="">Elige…</option>
					{#each scaleOpts as opt (opt.value)}
						<option value={opt.value}>{opt.label}</option>
					{/each}
				</select>
			</div>

			<div class="doc-subgrid">
				<label for={`rt-p-${row.id}`}>Probabilidad (0–2)</label>
				<select
					id={`rt-p-${row.id}`}
					aria-invalid={fb ? (fb.correct ? 'false' : 'true') : 'false'}
					value={entry.probability === null ? '' : String(entry.probability)}
					onchange={(e) =>
						patchRow(row.id, {
							probability: e.currentTarget.value === '' ? null : Number(e.currentTarget.value)
						})}
				>
					<option value="">Elige…</option>
					{#each scaleOpts as opt (opt.value)}
						<option value={opt.value}>{opt.label}</option>
					{/each}
				</select>
			</div>
		</div>

		{#if status}
			<p class="doc-risk-readout" class:low={status.acceptable} class:high={!status.acceptable}>
				<strong>Riesgo calculado: {status.level} / 4</strong> —
				{status.acceptable
					? `Aceptable (< ${spec.threshold})`
					: `No aceptable (≥ ${spec.threshold}, requiere tratamiento)`}
			</p>
		{/if}

		<ItemFeedbackNote feedback={fb} id={`fb-${row.id}`} />
	</fieldset>
{/each}
