<script lang="ts">
	import type { ItemFeedback, SoaDecision, SoaFormSpec } from './types';

	let {
		spec,
		answer,
		feedback = []
	}: {
		spec: SoaFormSpec;
		answer: { decisions: Record<string, SoaDecision> };
		feedback?: ItemFeedback[];
	} = $props();

	const byId = $derived(Object.fromEntries(feedback.map((item) => [item.id, item])));

	function decision(id: string): SoaDecision {
		return answer.decisions[id] ?? { applies: null, reason: '' };
	}

	function setApplies(id: string, applies: boolean) {
		answer.decisions[id] = { ...decision(id), applies };
	}

	function setReason(id: string, reason: string) {
		answer.decisions[id] = { ...decision(id), reason };
	}
</script>

<div class="scenario" data-testid="soa-scenario">
	<strong>Escenario.</strong>
	{spec.scenario}
</div>

<table>
	<thead>
		<tr>
			<th>Control</th>
			<th>¿Aplica?</th>
			<th>Justificación</th>
			<th><span class="sr">Resultado</span></th>
		</tr>
	</thead>
	<tbody>
		{#each spec.controls as control (control.id)}
			{@const fb = byId[control.id]}
			<tr class:ok={fb?.correct === true} class:bad={fb?.correct === false}>
				<td>{control.label}</td>
				<td>
					<fieldset>
						<legend class="sr">¿Aplica {control.label}?</legend>
						<label>
							<input
								type="radio"
								name={`ap-${control.id}`}
								checked={decision(control.id).applies === true}
								onchange={() => setApplies(control.id, true)}
							/>
							Sí
						</label>
						<label>
							<input
								type="radio"
								name={`ap-${control.id}`}
								checked={decision(control.id).applies === false}
								onchange={() => setApplies(control.id, false)}
							/>
							No
						</label>
					</fieldset>
				</td>
				<td>
					<select
						aria-label={`Justificación para ${control.label}`}
						value={decision(control.id).reason}
						onchange={(event) => setReason(control.id, event.currentTarget.value)}
					>
						<option value="">Elige…</option>
						{#each spec.reasons as reason (reason.id)}
							<option value={reason.id}>{reason.label}</option>
						{/each}
					</select>
					{#if fb}<p class="feedback">{fb.correct ? '✓' : '✗'} {fb.feedback}</p>{/if}
				</td>
				<td class="mark">{fb ? (fb.correct ? '✓' : '✗') : ''}</td>
			</tr>
		{/each}
	</tbody>
</table>

<style>
	.scenario {
		background: var(--bg);
		border: 1px solid var(--border);
		border-radius: 8px;
		padding: 10px 14px;
		margin-bottom: 14px;
	}

	table {
		width: 100%;
		border-collapse: collapse;
		margin-bottom: 14px;
		font-size: 0.93rem;
	}

	th,
	td {
		text-align: left;
		padding: 8px 10px;
		border-bottom: 1px solid var(--border);
		vertical-align: top;
	}

	th {
		color: var(--muted);
		font-size: 0.8rem;
		font-weight: 600;
	}

	tr.ok {
		background: #f2faf5;
	}

	tr.bad {
		background: #fdf4f3;
	}

	fieldset {
		border: none;
		padding: 0;
		margin: 0;
		display: flex;
		gap: 12px;
	}

	label {
		display: inline-flex;
		gap: 4px;
		align-items: center;
	}

	select {
		padding: 7px 8px;
		border: 1px solid var(--border);
		border-radius: 6px;
		font: inherit;
		background: #fff;
		max-width: 100%;
	}

	.feedback {
		margin: 6px 0 0;
		font-size: 0.85rem;
		color: var(--muted);
	}

	.mark {
		font-weight: 700;
		width: 1.5rem;
	}

	.sr {
		position: absolute;
		width: 1px;
		height: 1px;
		overflow: hidden;
		clip: rect(0 0 0 0);
		white-space: nowrap;
	}
</style>
