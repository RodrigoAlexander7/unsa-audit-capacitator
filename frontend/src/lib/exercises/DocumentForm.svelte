<script lang="ts">
	import ItemFeedbackNote from './ItemFeedbackNote.svelte';
	import type { DocumentFormAnswer, DocumentFormSpec, ItemFeedback } from './types';

	let {
		spec,
		answer,
		feedback = []
	}: {
		spec: DocumentFormSpec;
		answer: DocumentFormAnswer;
		feedback?: ItemFeedback[];
	} = $props();

	const byId = $derived(Object.fromEntries(feedback.map((item) => [item.id, item])));
	const fieldIds = $derived(
		new Set(spec.sections.flatMap((section) => section.fields.map((field) => field.id)))
	);
	const ruleFeedback = $derived(feedback.filter((item) => !fieldIds.has(item.id)));

	function strVal(id: string): string {
		const v = answer.fields[id];
		return typeof v === 'string' ? v : '';
	}

	function arrVal(id: string): string[] {
		const v = answer.fields[id];
		return Array.isArray(v) ? v : [];
	}

	function toggleMulti(fieldId: string, optionId: string, checked: boolean) {
		const current = arrVal(fieldId);
		answer.fields[fieldId] = checked
			? [...current.filter((x) => x !== optionId), optionId]
			: current.filter((x) => x !== optionId);
	}

	function describedBy(fieldId: string, hasHelp: boolean, hasFb: boolean): string | undefined {
		const ids = [hasHelp ? `help-${fieldId}` : '', hasFb ? `fb-${fieldId}` : ''].filter(Boolean);
		return ids.length ? ids.join(' ') : undefined;
	}
</script>

<div class="doc-scenario" data-testid="doc-scenario">
	<strong>Escenario.</strong>
	{spec.scenario}
</div>

<h3 class="doc-title">{spec.document_title}</h3>

{#each spec.sections as section (section.id)}
	<fieldset class="doc-section">
		<legend>{section.title}</legend>
		{#if section.description}
			<p class="doc-help">{section.description}</p>
		{/if}

		{#each section.fields as field (field.id)}
			{@const fb = byId[field.id]}
			{@const descId = describedBy(field.id, Boolean(field.help), Boolean(fb))}
			<div class="doc-field" class:ok={fb?.correct === true} class:bad={fb?.correct === false}>
				{#if field.type === 'multiselect'}
					<fieldset class="doc-multi" aria-describedby={descId}>
						<legend class="doc-sublegend">
							{field.label}{#if field.required}<span class="req" aria-hidden="true"> *</span><span
									class="sr"
								>
									(obligatorio)</span
								>{/if}
						</legend>
						{#if field.help}
							<p id={`help-${field.id}`} class="doc-help">{field.help}</p>
						{/if}
						<div class="doc-check-list">
							{#each field.options ?? [] as opt (opt.id)}
								<label class="doc-check">
									<input
										type="checkbox"
										value={opt.id}
										checked={arrVal(field.id).includes(opt.id)}
										onchange={(e) => toggleMulti(field.id, opt.id, e.currentTarget.checked)}
									/>
									<span>{opt.label}</span>
								</label>
							{/each}
						</div>
					</fieldset>
				{:else}
					<label for={`f-${field.id}`}>
						{field.label}{#if field.required}<span class="req" aria-hidden="true"> *</span><span
								class="sr"
							>
								(obligatorio)</span
							>{/if}
					</label>
					{#if field.help}
						<p id={`help-${field.id}`} class="doc-help">{field.help}</p>
					{/if}

					{#if field.type === 'textarea'}
						<textarea
							id={`f-${field.id}`}
							rows="4"
							placeholder={field.placeholder}
							required={field.required}
							aria-required={field.required ? 'true' : undefined}
							aria-invalid={fb ? (fb.correct ? 'false' : 'true') : 'false'}
							aria-describedby={descId}
							value={strVal(field.id)}
							oninput={(e) => (answer.fields[field.id] = e.currentTarget.value)}
						></textarea>
					{:else if field.type === 'date'}
						<input
							id={`f-${field.id}`}
							type="date"
							required={field.required}
							aria-required={field.required ? 'true' : undefined}
							aria-invalid={fb ? (fb.correct ? 'false' : 'true') : 'false'}
							aria-describedby={descId}
							value={strVal(field.id)}
							onchange={(e) => (answer.fields[field.id] = e.currentTarget.value)}
						/>
					{:else if field.type === 'select' || field.type === 'position' || field.type === 'reference'}
						<select
							id={`f-${field.id}`}
							required={field.required}
							aria-required={field.required ? 'true' : undefined}
							aria-invalid={fb ? (fb.correct ? 'false' : 'true') : 'false'}
							aria-describedby={descId}
							value={strVal(field.id)}
							onchange={(e) => (answer.fields[field.id] = e.currentTarget.value)}
						>
							<option value="">Elige…</option>
							{#each field.options ?? [] as opt (opt.id)}
								<option value={opt.id}>{opt.label}</option>
							{/each}
						</select>
					{:else}
						<input
							id={`f-${field.id}`}
							type="text"
							placeholder={field.placeholder}
							required={field.required}
							aria-required={field.required ? 'true' : undefined}
							aria-invalid={fb ? (fb.correct ? 'false' : 'true') : 'false'}
							aria-describedby={descId}
							value={strVal(field.id)}
							oninput={(e) => (answer.fields[field.id] = e.currentTarget.value)}
						/>
					{/if}
				{/if}

				<ItemFeedbackNote feedback={fb} id={`fb-${field.id}`} />
			</div>
		{/each}
	</fieldset>
{/each}

{#if ruleFeedback.length > 0}
	<section class="doc-rules" aria-labelledby="doc-rules-heading" data-testid="doc-cross-rules">
		<h4 id="doc-rules-heading">Reglas de coherencia entre campos</h4>
		<ul>
			{#each ruleFeedback as rule (rule.id)}
				<li class:ok={rule.correct} class:bad={!rule.correct}>
					<span role={rule.correct ? 'status' : 'alert'}>
						<strong>{rule.correct ? '✓' : '✗'}</strong>
						{rule.feedback}
					</span>
				</li>
			{/each}
		</ul>
	</section>
{/if}
