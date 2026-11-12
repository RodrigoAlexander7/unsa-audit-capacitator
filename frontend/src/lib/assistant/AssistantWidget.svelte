<script lang="ts">
	import { page } from '$app/state';
	import { tick } from 'svelte';
	import { errorMessage, type SessionUser } from '../api';
	import { renderMarkdown } from '../markdown';
	import {
		detectAssistantContext,
		resolveAliasesInText,
		type AdminAskResponse,
		type AssistantMessage,
		type CohortSummary,
		type CurriculumProposal,
		type GenerateProposalsResponse,
		type ProposalStatus
	} from './types';

	let { user }: { user: SessionUser } = $props();

	type AssistantMode = 'student' | 'admin';

	const ADMIN_SUGGESTIONS = [
		'¿Cómo avanzan los estudiantes estancados y qué seguimiento requieren?',
		'¿Qué módulos concentran más fallos en el cohorte?',
		'¿Qué debilidades muestra el cohorte en las evaluaciones controller/processor?'
	];

	const STATUS_LABEL: Record<ProposalStatus, string> = {
		draft: 'Borrador',
		accepted: 'Aceptada',
		discarded: 'Descartada'
	};

	const ROUTE_OPTIONS = [
		{ value: '', label: 'Todas las rutas' },
		{ value: 'sensibilizacion', label: 'Ruta 1 · Sensibilización' },
		{ value: 'interpretacion', label: 'Ruta 2 · Interpretación' },
		{ value: 'implementacion', label: 'Ruta 3 · Implementación' },
		{ value: 'auditor', label: 'Ruta 4 · Auditor interno' }
	];

	let isOpen = $state(false);
	let mode = $state<AssistantMode>('student');
	let loadedStudentHistory = $state(false);
	let loadedAdminData = $state(false);
	let loading = $state(false);
	let clearing = $state(false);
	let generatingProposals = $state(false);
	let reviewingId = $state<string | null>(null);
	let question = $state('');
	let targetRoute = $state('');
	let errorText = $state<string | null>(null);
	let proposalSummary = $state<string | null>(null);

	let studentMessages = $state<AssistantMessage[]>([]);
	let adminMessages = $state<AssistantMessage[]>([]);
	let cohort = $state<CohortSummary | null>(null);
	let proposals = $state<CurriculumProposal[]>([]);

	let triggerEl: HTMLButtonElement | undefined = $state();
	let dialogEl: HTMLDialogElement | undefined = $state();
	let inputEl: HTMLTextAreaElement | undefined = $state();
	let logEl: HTMLDivElement | undefined = $state();

	const isSuperadmin = $derived(user.role === 'superadmin');
	const contextHint = $derived(detectAssistantContext(page.url.pathname, page.params));
	const activeMessages = $derived(mode === 'admin' ? adminMessages : studentMessages);
	const orderedMessages = $derived([...activeMessages].reverse());
	const aliases = $derived(cohort?.aliases ?? []);

	function showNativePanel(el: HTMLDialogElement): void {
		if ('showPopover' in el && typeof el.showPopover === 'function') {
			if (!el.matches(':popover-open')) el.showPopover();
		} else if (!el.open) {
			el.show();
		}
	}

	function hideNativePanel(el: HTMLDialogElement): void {
		if ('hidePopover' in el && typeof el.hidePopover === 'function') {
			if (el.matches(':popover-open')) el.hidePopover();
		} else if (el.open) {
			el.close();
		}
	}

	async function scrollLogToBottom(): Promise<void> {
		await tick();
		if (logEl) logEl.scrollTop = logEl.scrollHeight;
	}

	async function fetchStudentHistory(): Promise<void> {
		if (loadedStudentHistory) return;
		try {
			const res = await fetch('/assistant/history');
			if (res.ok) {
				studentMessages = (await res.json()) as AssistantMessage[];
				loadedStudentHistory = true;
				await scrollLogToBottom();
			}
		} catch {
			// Mantiene estado silencioso al abrir si la red falla temporalmente.
		}
	}

	async function fetchAdminData(): Promise<void> {
		if (!isSuperadmin || loadedAdminData) return;
		try {
			const [cohortRes, histRes, propRes] = await Promise.all([
				fetch('/assistant/admin/cohort'),
				fetch('/assistant/admin/history'),
				fetch('/assistant/admin/proposals')
			]);
			if (cohortRes.ok) cohort = (await cohortRes.json()) as CohortSummary;
			if (histRes.ok) adminMessages = (await histRes.json()) as AssistantMessage[];
			if (propRes.ok) proposals = (await propRes.json()) as CurriculumProposal[];
			loadedAdminData = true;
			await scrollLogToBottom();
		} catch {
			// Reintenta manualmente en la siguiente acción.
		}
	}

	async function openPanel(): Promise<void> {
		if (!dialogEl) return;
		isOpen = true;
		showNativePanel(dialogEl);
		await tick();
		inputEl?.focus();
		if (mode === 'admin' && isSuperadmin) await fetchAdminData();
		else await fetchStudentHistory();
	}

	function closePanel(): void {
		if (dialogEl) hideNativePanel(dialogEl);
		isOpen = false;
		triggerEl?.focus();
	}

	function togglePanel(): void {
		if (isOpen) closePanel();
		else void openPanel();
	}

	function switchMode(nextMode: AssistantMode): void {
		if (!isSuperadmin && nextMode === 'admin') return;
		mode = nextMode;
		errorText = null;
		if (nextMode === 'admin') void fetchAdminData();
		else void fetchStudentHistory();
	}

	function onDialogKeydown(event: KeyboardEvent): void {
		if (event.key === 'Escape' && isOpen) {
			event.preventDefault();
			closePanel();
		}
	}

	function onTabKeydown(event: KeyboardEvent): void {
		if (!isSuperadmin) return;
		if (event.key === 'ArrowRight' || event.key === 'ArrowLeft') {
			event.preventDefault();
			switchMode(mode === 'student' ? 'admin' : 'student');
		}
	}

	function displayText(raw: string): string {
		if (mode !== 'admin') return raw;
		return resolveAliasesInText(raw, aliases);
	}

	async function sendQuestion(textToSend?: string): Promise<void> {
		const clean = (textToSend ?? question).trim();
		if (!clean || loading) return;
		if (clean.length > 800) {
			errorText = 'La consulta no puede superar los 800 caracteres.';
			return;
		}
		loading = true;
		errorText = null;
		try {
			if (mode === 'admin' && isSuperadmin) {
				const res = await fetch('/assistant/admin/ask', {
					method: 'POST',
					headers: { 'Content-Type': 'application/json' },
					body: JSON.stringify({ question: clean })
				});
				const parsed = (await res.json().catch(() => null)) as AdminAskResponse | null;
				if (!res.ok || !parsed?.message) {
					errorText = errorMessage(parsed, 'No se pudo obtener respuesta del coordinador.');
					return;
				}
				adminMessages = [parsed.message, ...adminMessages];
				if (Array.isArray(parsed.aliases)) {
					cohort = {
						total_learners: parsed.aliases.length,
						stalled_count: parsed.aliases.filter((a) => a.stalled).length,
						aliases: parsed.aliases
					};
				}
				loadedAdminData = true;
			} else {
				const res = await fetch('/assistant/ask', {
					method: 'POST',
					headers: { 'Content-Type': 'application/json' },
					body: JSON.stringify({
						question: clean,
						module_id: contextHint.moduleId,
						route_path: contextHint.routePath
					})
				});
				const parsed = await res.json().catch(() => null);
				if (!res.ok || !parsed) {
					errorText = errorMessage(parsed, 'No se pudo obtener respuesta del asistente.');
					return;
				}
				studentMessages = [parsed as AssistantMessage, ...studentMessages];
				loadedStudentHistory = true;
			}
			question = '';
			await scrollLogToBottom();
		} catch {
			errorText = 'Error de conexión al consultar al asistente.';
		} finally {
			loading = false;
		}
	}

	async function clearHistory(): Promise<void> {
		if (clearing || activeMessages.length === 0) return;
		clearing = true;
		errorText = null;
		const endpoint = mode === 'admin' && isSuperadmin ? '/assistant/admin/history' : '/assistant/history';
		try {
			const res = await fetch(endpoint, { method: 'DELETE' });
			if (res.ok) {
				if (mode === 'admin' && isSuperadmin) adminMessages = [];
				else studentMessages = [];
			} else {
				errorText = 'No se pudo limpiar el historial.';
			}
		} catch {
			errorText = 'Error de conexión al limpiar el historial.';
		} finally {
			clearing = false;
		}
	}

	async function generateProposals(): Promise<void> {
		if (!isSuperadmin || generatingProposals) return;
		generatingProposals = true;
		errorText = null;
		proposalSummary = null;
		try {
			const focus = question.trim() || null;
			const res = await fetch('/assistant/admin/proposals/generate', {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({
					focus,
					route_code: targetRoute || null
				})
			});
			const parsed = (await res.json().catch(() => null)) as GenerateProposalsResponse | null;
			if (!res.ok || !parsed?.proposals) {
				errorText = errorMessage(parsed, 'No se pudieron generar propuestas de reestructuración.');
				return;
			}
			proposalSummary = parsed.summary;
			proposals = [...parsed.proposals, ...proposals];
		} catch {
			errorText = 'Error de conexión al generar propuestas.';
		} finally {
			generatingProposals = false;
		}
	}

	async function reviewProposal(id: string, nextStatus: ProposalStatus): Promise<void> {
		if (!isSuperadmin || reviewingId) return;
		reviewingId = id;
		errorText = null;
		try {
			const res = await fetch(`/assistant/admin/proposals/${id}`, {
				method: 'PATCH',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({ status: nextStatus })
			});
			const updated = (await res.json().catch(() => null)) as CurriculumProposal | null;
			if (!res.ok || !updated?.id) {
				errorText = errorMessage(updated, 'No se pudo actualizar la propuesta.');
				return;
			}
			proposals = proposals.map((p) => (p.id === id ? updated : p));
		} catch {
			errorText = 'Error de conexión al revisar la propuesta.';
		} finally {
			reviewingId = null;
		}
	}

	function handleSubmit(event: SubmitEvent): void {
		event.preventDefault();
		void sendQuestion();
	}
</script>

<aside aria-label="Asistente de capacitación">
	<button
		type="button"
		bind:this={triggerEl}
		class="assistant-fab"
		aria-expanded={isOpen}
		aria-controls="assistant-panel"
		data-testid="assistant-fab"
		onclick={togglePanel}
	>
		{isOpen ? 'Ocultar asistente' : 'Asistente UNSA'}
	</button>

	<dialog
		id="assistant-panel"
		bind:this={dialogEl}
		popover="manual"
		class="assistant-panel"
		aria-labelledby="assistant-panel-title"
		data-testid="assistant-panel"
		onkeydown={onDialogKeydown}
	>
		<header class="assistant-header">
			<div class="assistant-heading">
				<h2 id="assistant-panel-title">
					{mode === 'admin' ? 'Asistente coordinador · Cohorte' : 'Asistente UNSA · PIMS'}
				</h2>
				<p class="assistant-ctx" data-testid="assistant-context-label">
					{mode === 'admin'
						? 'Consulta seudonimizada (P-xx) y reestructuración'
						: `${contextHint.label} · ${user.full_name}`}
				</p>
			</div>
			<div class="assistant-actions">
				<button
					type="button"
					class="btn-secondary"
					disabled={loading || clearing || activeMessages.length === 0}
					onclick={clearHistory}
					data-testid="assistant-clear"
				>
					Limpiar
				</button>
				<button
					type="button"
					class="btn-close"
					onclick={closePanel}
					data-testid="assistant-close"
				>
					Cerrar
				</button>
			</div>
		</header>

		{#if isSuperadmin}
			<!-- svelte-ignore a11y_interactive_supports_focus -->
			<div
				class="mode-tabs"
				role="tablist"
				aria-label="Modo del asistente"
				onkeydown={onTabKeydown}
			>
				<button
					type="button"
					id="tab-student"
					role="tab"
					aria-selected={mode === 'student'}
					aria-controls="assistant-panel-body"
					class="tab-btn"
					class:active={mode === 'student'}
					onclick={() => switchMode('student')}
					data-testid="assistant-tab-student"
				>
					Estudiante
				</button>
				<button
					type="button"
					id="tab-admin"
					role="tab"
					aria-selected={mode === 'admin'}
					aria-controls="assistant-panel-body"
					class="tab-btn"
					class:active={mode === 'admin'}
					onclick={() => switchMode('admin')}
					data-testid="assistant-tab-admin"
				>
					Administrador
				</button>
			</div>
		{/if}

		<!-- svelte-ignore a11y_no_noninteractive_tabindex -->
		<div
			id="assistant-panel-body"
			class="assistant-body"
			bind:this={logEl}
			role={isSuperadmin ? 'tabpanel' : 'region'}
			aria-labelledby={isSuperadmin ? (mode === 'admin' ? 'tab-admin' : 'tab-student') : 'assistant-panel-title'}
			tabindex="0"
		>
			{#if mode === 'admin' && isSuperadmin}
				{#if cohort}
					<section class="cohort-box" aria-label="Resumen del cohorte" data-testid="admin-cohort-summary">
						<p class="cohort-kpi">
							<strong>{cohort.total_learners}</strong> participantes ·
							<strong>{cohort.stalled_count}</strong> estancados (alias P-xx hacia IA)
						</p>
						<details class="alias-dir" data-testid="admin-alias-directory">
							<summary>Directorio seudónimo local ({cohort.aliases.length})</summary>
							<ul class="alias-list">
								{#each cohort.aliases as entry (entry.alias)}
									<li>
										<button
											type="button"
											class="alias-pill"
											onclick={() =>
												(question = `¿Cómo avanza ${entry.alias} y qué seguimiento recomiendas?`)}
										>
											<span class="alias-code">{entry.alias}</span>
											<span>{entry.full_name} · {entry.overall_progress_pct} %</span>
											{#if entry.stalled}
												<span class="badge-stalled">estancado</span>
											{/if}
										</button>
									</li>
								{/each}
							</ul>
						</details>
					</section>
				{/if}
			{/if}

			<div class="assistant-log" role="log" aria-live="polite" data-testid="assistant-log">
				{#if orderedMessages.length === 0}
					<p class="empty-hint">
						{#if mode === 'admin'}
							Consulta el progreso del cohorte usando alias P-xx o nombres (el servidor seudonimiza antes de consultar a la IA).
						{:else}
							Pregúntame sobre ISO/IEC 27701, criterios de auditoría o la estructura ficticia de la UNSA.
							No entrego respuestas exactas de los ejercicios evaluados.
						{/if}
					</p>
					<div class="chips" aria-label="Consultas sugeridas">
						{#each mode === 'admin' ? ADMIN_SUGGESTIONS : contextHint.suggestions as suggestion (suggestion)}
							<button
								type="button"
								class="chip-btn"
								disabled={loading}
								onclick={() => sendQuestion(suggestion)}
							>
								{suggestion}
							</button>
						{/each}
					</div>
				{:else}
					<ul class="msg-list">
						{#each orderedMessages as msg (msg.id)}
							<li class="msg-item" data-testid="assistant-msg">
								<p class="msg-question">
									<strong>Tú:</strong> {displayText(msg.question)}
								</p>
								{#if msg.status === 'ok' && msg.answer}
									<div class="msg-answer">
										<!-- eslint-disable-next-line svelte/no-at-html-tags -- Markdown sanitizado -->
										{@html renderMarkdown(displayText(msg.answer))}
									</div>
								{:else if msg.status === 'refused' && msg.answer}
									<p class="msg-refused" data-testid="assistant-refused">{msg.answer}</p>
								{:else}
									<p class="msg-err">
										Error: {msg.error ?? 'No se pudo obtener respuesta en este intento.'}
									</p>
								{/if}
							</li>
						{/each}
					</ul>
				{/if}
			</div>

			{#if mode === 'admin' && isSuperadmin}
				<section
					class="proposals-box"
					aria-labelledby="proposals-heading"
					data-testid="admin-proposals-section"
				>
					<div class="proposals-head">
						<h3 id="proposals-heading">Borradores de reestructuración ({proposals.length})</h3>
						<button
							type="button"
							class="btn-propose"
							disabled={generatingProposals || loading}
							onclick={generateProposals}
							data-testid="admin-generate-proposals"
						>
							{generatingProposals ? 'Generando…' : 'Proponer ajuste'}
						</button>
					</div>
					<div class="route-filter">
						<label for="proposal-route-select">Enfoque por ruta</label>
						<select id="proposal-route-select" bind:value={targetRoute}>
							{#each ROUTE_OPTIONS as opt (opt.value)}
								<option value={opt.value}>{opt.label}</option>
							{/each}
						</select>
					</div>
					{#if proposalSummary}
						<p class="status-inline" role="status">{displayText(proposalSummary)}</p>
					{/if}
					{#if proposals.length === 0}
						<p class="empty-proposals">
							Aún no hay borradores. «Proponer ajuste» genera sugerencias revisables sin alterar el currículo activo.
						</p>
					{:else}
						<ul class="proposal-list">
							{#each proposals as prop (prop.id)}
								<li class="proposal-card" data-testid="admin-proposal-card">
									<div class="proposal-top">
										<strong>{prop.title}</strong>
										<span class={`status-badge status-${prop.status}`} data-testid="proposal-status">
											{STATUS_LABEL[prop.status] ?? prop.status}
										</span>
									</div>
									{#if prop.target_route_code || prop.target_module_slug}
										<p class="proposal-meta">
											{prop.target_route_code ?? 'plan general'}
											{prop.target_module_slug ? `· ${prop.target_module_slug}` : ''}
										</p>
									{/if}
									<p class="proposal-text">{displayText(prop.proposed_change)}</p>
									<p class="proposal-rationale"><em>Base:</em> {displayText(prop.rationale)}</p>
									<div class="proposal-actions">
										<button
											type="button"
											class="btn-accept"
											disabled={reviewingId === prop.id || prop.status === 'accepted'}
											onclick={() => reviewProposal(prop.id, 'accepted')}
											data-testid="proposal-accept"
										>
											Aceptar
										</button>
										<button
											type="button"
											class="btn-discard"
											disabled={reviewingId === prop.id || prop.status === 'discarded'}
											onclick={() => reviewProposal(prop.id, 'discarded')}
											data-testid="proposal-discard"
										>
											Descartar
										</button>
									</div>
								</li>
							{/each}
						</ul>
					{/if}
				</section>
			{/if}
		</div>

		{#if loading}
			<p class="status-note" role="status" data-testid="assistant-loading">
				Consultando al asistente…
			</p>
		{/if}
		{#if errorText}
			<p class="error-note" role="alert" data-testid="assistant-error">{errorText}</p>
		{/if}

		<form class="assistant-form" onsubmit={handleSubmit}>
			<label for="assistant-question" class="field-label">
				{mode === 'admin' ? 'Consulta sobre el cohorte o foco de ajuste' : 'Tu consulta'}
			</label>
			<div class="composer-row">
				<textarea
					id="assistant-question"
					bind:this={inputEl}
					bind:value={question}
					rows="2"
					maxlength={800}
					placeholder={mode === 'admin'
						? 'Ej. ¿Por qué P-02 o Carmen se estancaron en Ruta 1?'
						: 'Ej. ¿Qué unidades UNSA intervienen en este proceso?'}
					disabled={loading}
					data-testid="assistant-input"
				></textarea>
				<button
					type="submit"
					class="btn-send"
					disabled={loading || !question.trim()}
					data-testid="assistant-submit"
				>
					Enviar
				</button>
			</div>
		</form>
	</dialog>
</aside>

<style>
	.assistant-fab {
		position: fixed;
		right: 20px;
		bottom: 20px;
		z-index: 40;
		background: var(--primary);
		color: var(--primary-contrast);
		border: 2px solid #0f3668;
		border-radius: 999px;
		padding: 10px 18px;
		font: inherit;
		font-weight: 600;
		font-size: 0.95rem;
		cursor: pointer;
		box-shadow: 0 6px 20px rgba(17, 36, 62, 0.22);
	}

	.assistant-fab:focus-visible,
	.btn-close:focus-visible,
	.btn-secondary:focus-visible,
	.tab-btn:focus-visible,
	.alias-pill:focus-visible,
	.btn-propose:focus-visible,
	.btn-accept:focus-visible,
	.btn-discard:focus-visible,
	.chip-btn:focus-visible,
	.btn-send:focus-visible,
	select:focus-visible,
	textarea:focus-visible {
		outline: 3px solid #0b3a75;
		outline-offset: 2px;
	}

	.assistant-panel {
		position: fixed;
		inset: auto 20px 76px auto;
		margin: 0;
		padding: 0;
		width: min(470px, calc(100vw - 24px));
		max-height: min(80vh, 650px);
		background: var(--surface);
		color: var(--text);
		border: 1px solid var(--border);
		border-radius: var(--radius);
		box-shadow: 0 14px 36px rgba(17, 36, 62, 0.2);
	}

	.assistant-panel[open],
	.assistant-panel:popover-open {
		display: flex;
		flex-direction: column;
	}

	.assistant-header {
		display: flex;
		align-items: flex-start;
		justify-content: space-between;
		gap: 8px;
		padding: 12px 14px;
		border-bottom: 1px solid var(--border);
		background: #f3f6fb;
		border-radius: var(--radius) var(--radius) 0 0;
	}

	.assistant-heading h2 {
		margin: 0;
		font-size: 1rem;
		color: var(--text);
	}

	.assistant-ctx {
		margin: 2px 0 0;
		font-size: 0.78rem;
		color: #465162;
	}

	.assistant-actions {
		display: flex;
		gap: 6px;
		flex-shrink: 0;
	}

	.mode-tabs {
		display: grid;
		grid-template-columns: 1fr 1fr;
		gap: 4px;
		padding: 6px 14px;
		background: #eef2f8;
		border-bottom: 1px solid var(--border);
	}

	.tab-btn {
		background: transparent;
		color: #2f3b4c;
		border: 1px solid transparent;
		border-radius: 6px;
		padding: 5px 8px;
		font: inherit;
		font-size: 0.84rem;
		font-weight: 600;
		cursor: pointer;
	}

	.tab-btn.active {
		background: var(--surface);
		color: #0f3668;
		border-color: #b9cbe6;
	}

	.btn-secondary,
	.btn-close {
		background: var(--surface);
		color: var(--text);
		border: 1px solid #96a3b5;
		border-radius: 6px;
		padding: 4px 10px;
		font: inherit;
		font-size: 0.82rem;
		font-weight: 500;
		cursor: pointer;
	}

	.btn-secondary:disabled {
		opacity: 0.5;
		cursor: not-allowed;
	}

	.assistant-body {
		flex: 1;
		overflow-y: auto;
		padding: 10px 14px;
		display: flex;
		flex-direction: column;
		gap: 12px;
		min-height: 190px;
	}

	.cohort-box {
		background: #f6f8fc;
		border: 1px solid var(--border);
		border-radius: 8px;
		padding: 8px 10px;
		font-size: 0.82rem;
	}

	.cohort-kpi {
		margin: 0 0 4px;
	}

	.alias-dir summary {
		cursor: pointer;
		font-weight: 600;
		color: #153e75;
	}

	.alias-list {
		list-style: none;
		padding: 6px 0 0;
		margin: 0;
		display: flex;
		flex-direction: column;
		gap: 4px;
		max-height: 140px;
		overflow-y: auto;
	}

	.alias-pill {
		width: 100%;
		display: flex;
		align-items: center;
		gap: 6px;
		text-align: left;
		background: var(--surface);
		color: var(--text);
		border: 1px solid #cdd6e4;
		border-radius: 6px;
		padding: 4px 8px;
		font: inherit;
		font-size: 0.78rem;
		cursor: pointer;
	}

	.alias-code {
		font-weight: 700;
		color: #153e75;
	}

	.badge-stalled {
		margin-left: auto;
		background: #fef6ea;
		color: #7c3a04;
		border: 1px solid #d97706;
		border-radius: 999px;
		padding: 0 6px;
		font-size: 0.72rem;
		font-weight: 600;
	}

	.assistant-log {
		display: flex;
		flex-direction: column;
		gap: 8px;
	}

	.empty-hint {
		margin: 0 0 8px;
		font-size: 0.86rem;
		color: #465162;
	}

	.chips {
		display: flex;
		flex-direction: column;
		gap: 6px;
	}

	.chip-btn {
		text-align: left;
		background: #eef3fb;
		color: #153e75;
		border: 1px solid #b9cbe6;
		border-radius: 8px;
		padding: 7px 10px;
		font: inherit;
		font-size: 0.83rem;
		cursor: pointer;
	}

	.msg-list {
		list-style: none;
		padding: 0;
		margin: 0;
		display: flex;
		flex-direction: column;
		gap: 10px;
	}

	.msg-item {
		display: flex;
		flex-direction: column;
		gap: 6px;
	}

	.msg-question {
		margin: 0;
		background: #eef3fb;
		color: var(--text);
		padding: 8px 10px;
		border-radius: 8px;
		font-size: 0.86rem;
	}

	.msg-answer {
		background: var(--surface);
		border: 1px solid var(--border);
		border-radius: 8px;
		padding: 8px 10px;
		font-size: 0.86rem;
	}

	.msg-answer :global(p:first-child) {
		margin-top: 0;
	}

	.msg-answer :global(p:last-child) {
		margin-bottom: 0;
	}

	.msg-refused {
		margin: 0;
		background: #fef6ea;
		color: #7c3a04;
		border: 1px solid #d97706;
		border-radius: 8px;
		padding: 8px 10px;
		font-size: 0.85rem;
	}

	.msg-err {
		margin: 0;
		background: #fff4f2;
		color: #9e1c13;
		border: 1px solid #e0a19c;
		border-radius: 8px;
		padding: 8px 10px;
		font-size: 0.85rem;
	}

	.proposals-box {
		border-top: 1px solid var(--border);
		padding-top: 10px;
	}

	.proposals-head {
		display: flex;
		align-items: center;
		justify-content: space-between;
		gap: 8px;
		margin-bottom: 6px;
	}

	.proposals-head h3 {
		margin: 0;
		font-size: 0.88rem;
		color: var(--text);
	}

	.btn-propose {
		background: #153e75;
		color: #ffffff;
		border: 0;
		border-radius: 6px;
		padding: 5px 10px;
		font: inherit;
		font-size: 0.78rem;
		font-weight: 600;
		cursor: pointer;
	}

	.btn-propose:disabled {
		opacity: 0.55;
		cursor: not-allowed;
	}

	.route-filter {
		display: flex;
		align-items: center;
		gap: 8px;
		margin-bottom: 8px;
		font-size: 0.78rem;
	}

	.route-filter select {
		flex: 1;
		font: inherit;
		font-size: 0.78rem;
		padding: 3px 6px;
		border: 1px solid #9aa6b8;
		border-radius: 6px;
		background: var(--surface);
		color: var(--text);
	}

	.status-inline {
		margin: 0 0 8px;
		font-size: 0.8rem;
		color: #145a2d;
		background: #e9f7ee;
		padding: 5px 8px;
		border-radius: 6px;
	}

	.empty-proposals {
		margin: 0;
		font-size: 0.8rem;
		color: #465162;
	}

	.proposal-list {
		list-style: none;
		padding: 0;
		margin: 0;
		display: flex;
		flex-direction: column;
		gap: 8px;
	}

	.proposal-card {
		border: 1px solid var(--border);
		border-radius: 8px;
		padding: 8px 10px;
		background: #fcfdff;
		font-size: 0.82rem;
	}

	.proposal-top {
		display: flex;
		align-items: flex-start;
		justify-content: space-between;
		gap: 8px;
	}

	.status-badge {
		border-radius: 999px;
		padding: 1px 8px;
		font-size: 0.72rem;
		font-weight: 700;
		flex-shrink: 0;
	}

	.status-draft {
		background: #eef3fb;
		color: #153e75;
		border: 1px solid #b9cbe6;
	}

	.status-accepted {
		background: #e9f7ee;
		color: #145a2d;
		border: 1px solid #9ad0ad;
	}

	.status-discarded {
		background: #f3f4f6;
		color: #465162;
		border: 1px solid #cbd5e1;
	}

	.proposal-meta {
		margin: 2px 0 4px;
		font-size: 0.75rem;
		color: #465162;
	}

	.proposal-text,
	.proposal-rationale {
		margin: 4px 0;
	}

	.proposal-actions {
		display: flex;
		gap: 6px;
		margin-top: 6px;
	}

	.btn-accept,
	.btn-discard {
		font: inherit;
		font-size: 0.76rem;
		font-weight: 600;
		padding: 3px 9px;
		border-radius: 6px;
		cursor: pointer;
	}

	.btn-accept {
		background: #e9f7ee;
		color: #145a2d;
		border: 1px solid #72b38a;
	}

	.btn-discard {
		background: #f3f4f6;
		color: #364152;
		border: 1px solid #b5c0cf;
	}

	.btn-accept:disabled,
	.btn-discard:disabled {
		opacity: 0.5;
		cursor: not-allowed;
	}

	.status-note {
		margin: 0;
		padding: 4px 14px;
		font-size: 0.82rem;
		color: #153e75;
	}

	.error-note {
		margin: 0;
		padding: 6px 14px;
		font-size: 0.82rem;
		color: #9e1c13;
		background: #fff4f2;
	}

	.assistant-form {
		padding: 10px 14px 12px;
		border-top: 1px solid var(--border);
		background: #f9fafc;
		border-radius: 0 0 var(--radius) var(--radius);
	}

	.field-label {
		display: block;
		font-size: 0.8rem;
		font-weight: 600;
		color: var(--text);
		margin-bottom: 4px;
	}

	.composer-row {
		display: flex;
		gap: 8px;
		align-items: flex-end;
	}

	textarea {
		flex: 1;
		font: inherit;
		font-size: 0.86rem;
		padding: 7px 9px;
		border: 1px solid #9aa6b8;
		border-radius: 6px;
		background: var(--surface);
		color: var(--text);
		resize: vertical;
	}

	.btn-send {
		background: var(--primary);
		color: var(--primary-contrast);
		border: 0;
		border-radius: 6px;
		padding: 8px 14px;
		font: inherit;
		font-size: 0.86rem;
		font-weight: 600;
		cursor: pointer;
	}

	.btn-send:disabled {
		opacity: 0.55;
		cursor: not-allowed;
	}
</style>
