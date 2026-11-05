<script lang="ts">
	import ItemFeedbackNote from './ItemFeedbackNote.svelte';
	import type {
		AuditChecklistAnswer,
		AuditChecklistSpec,
		AuditItemAnswer,
		ItemFeedback
	} from './types';

	let {
		spec,
		answer,
		feedback = []
	}: {
		spec: AuditChecklistSpec;
		answer: AuditChecklistAnswer;
		feedback?: ItemFeedback[];
	} = $props();

	const byId = $derived(Object.fromEntries(feedback.map((item) => [item.id, item])));

	function itemAns(id: string): AuditItemAnswer {
		return answer.items[id] ?? { question_id: '', evidence_id: '', verdict: '' };
	}

	function patchItem(id: string, patch: Partial<AuditItemAnswer>) {
		answer.items[id] = { ...itemAns(id), ...patch };
	}
</script>

<div class="doc-scenario" data-testid="audit-scenario">
	<strong>Escenario.</strong>
	{spec.scenario}
</div>

{#each spec.items as item (item.id)}
	{@const entry = itemAns(item.id)}
	{@const fb = byId[item.id]}
	<fieldset class="doc-card" class:ok={fb?.correct === true} class:bad={fb?.correct === false}>
		<legend>
			<span class="doc-pill">{item.clause_ref}</span>
			{item.requirement_title}
		</legend>

		<p class="doc-context">
			<strong>Situación observada en UNSA:</strong>
			{item.observed_context}
		</p>

		<div class="doc-field">
			<label for={`ac-q-${item.id}`}>Pregunta de auditoría</label>
			<select
				id={`ac-q-${item.id}`}
				aria-invalid={fb ? (fb.correct ? 'false' : 'true') : 'false'}
				value={entry.question_id}
				onchange={(e) => patchItem(item.id, { question_id: e.currentTarget.value })}
			>
				<option value="">Elige pregunta…</option>
				{#each item.questions as q (q.id)}
					<option value={q.id}>{q.label}</option>
				{/each}
			</select>
		</div>

		<div class="doc-field">
			<label for={`ac-e-${item.id}`}>Evidencia objetiva a solicitar</label>
			<select
				id={`ac-e-${item.id}`}
				aria-invalid={fb ? (fb.correct ? 'false' : 'true') : 'false'}
				value={entry.evidence_id}
				onchange={(e) => patchItem(item.id, { evidence_id: e.currentTarget.value })}
			>
				<option value="">Elige evidencia…</option>
				{#each item.evidences as ev (ev.id)}
					<option value={ev.id}>{ev.label}</option>
				{/each}
			</select>
		</div>

		<div class="doc-field">
			<label for={`ac-v-${item.id}`}>Veredicto de auditoría</label>
			<select
				id={`ac-v-${item.id}`}
				aria-invalid={fb ? (fb.correct ? 'false' : 'true') : 'false'}
				value={entry.verdict}
				onchange={(e) => patchItem(item.id, { verdict: e.currentTarget.value })}
			>
				<option value="">Elige veredicto…</option>
				{#each spec.verdicts as v (v.id)}
					<option value={v.id}>{v.label}</option>
				{/each}
			</select>
		</div>

		<ItemFeedbackNote feedback={fb} id={`fb-${item.id}`} />
	</fieldset>
{/each}
