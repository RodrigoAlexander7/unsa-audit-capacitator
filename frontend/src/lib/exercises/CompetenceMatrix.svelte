<script lang="ts">
	import ItemFeedbackNote from './ItemFeedbackNote.svelte';
	import type {
		CompetenceMatrixAnswer,
		CompetenceMatrixSpec,
		CompetenceRowAnswer,
		ItemFeedback
	} from './types';

	let {
		spec,
		answer,
		feedback = []
	}: {
		spec: CompetenceMatrixSpec;
		answer: CompetenceMatrixAnswer;
		feedback?: ItemFeedback[];
	} = $props();

	const byId = $derived(Object.fromEntries(feedback.map((item) => [item.id, item])));

	function rowAns(id: string): CompetenceRowAnswer {
		return (
			answer.rows[id] ?? {
				competency_id: '',
				training_id: '',
				evidence_id: '',
				...(spec.evaluators ? { evaluator_id: '' } : {})
			}
		);
	}

	function patchRow(id: string, patch: Partial<CompetenceRowAnswer>) {
		answer.rows[id] = { ...rowAns(id), ...patch };
	}
</script>

<div class="doc-scenario" data-testid="competence-scenario">
	<strong>Escenario.</strong>
	{spec.scenario}
</div>

{#each spec.rows as row (row.id)}
	{@const entry = rowAns(row.id)}
	{@const fb = byId[row.id]}
	<fieldset class="doc-card" class:ok={fb?.correct === true} class:bad={fb?.correct === false}>
		<legend>{row.position_title}</legend>

		{#if row.role_summary}
			<p class="doc-help">{row.role_summary}</p>
		{/if}

		<div class="doc-grid">
			<div class="doc-subgrid">
				<label for={`cm-comp-${row.id}`}>Competencia requerida</label>
				<select
					id={`cm-comp-${row.id}`}
					aria-invalid={fb ? (fb.correct ? 'false' : 'true') : 'false'}
					value={entry.competency_id}
					onchange={(e) => patchRow(row.id, { competency_id: e.currentTarget.value })}
				>
					<option value="">Elige competencia…</option>
					{#each spec.competencies as opt (opt.id)}
						<option value={opt.id}>{opt.label}</option>
					{/each}
				</select>
			</div>

			<div class="doc-subgrid">
				<label for={`cm-trn-${row.id}`}>Capacitación / formación</label>
				<select
					id={`cm-trn-${row.id}`}
					aria-invalid={fb ? (fb.correct ? 'false' : 'true') : 'false'}
					value={entry.training_id}
					onchange={(e) => patchRow(row.id, { training_id: e.currentTarget.value })}
				>
					<option value="">Elige capacitación…</option>
					{#each spec.trainings as opt (opt.id)}
						<option value={opt.id}>{opt.label}</option>
					{/each}
				</select>
			</div>

			<div class="doc-subgrid">
				<label for={`cm-ev-${row.id}`}>Evidencia de eficacia</label>
				<select
					id={`cm-ev-${row.id}`}
					aria-invalid={fb ? (fb.correct ? 'false' : 'true') : 'false'}
					value={entry.evidence_id}
					onchange={(e) => patchRow(row.id, { evidence_id: e.currentTarget.value })}
				>
					<option value="">Elige evidencia…</option>
					{#each spec.evidences as opt (opt.id)}
						<option value={opt.id}>{opt.label}</option>
					{/each}
				</select>
			</div>

			{#if spec.evaluators}
				<div class="doc-subgrid">
					<label for={`cm-eval-${row.id}`}>Evaluador independiente</label>
					<select
						id={`cm-eval-${row.id}`}
						aria-invalid={fb ? (fb.correct ? 'false' : 'true') : 'false'}
						value={entry.evaluator_id ?? ''}
						onchange={(e) => patchRow(row.id, { evaluator_id: e.currentTarget.value })}
					>
						<option value="">Elige evaluador…</option>
						{#each spec.evaluators as opt (opt.id)}
							<option value={opt.id}>{opt.label}</option>
						{/each}
					</select>
				</div>
			{/if}
		</div>

		<ItemFeedbackNote feedback={fb} id={`fb-${row.id}`} />
	</fieldset>
{/each}
