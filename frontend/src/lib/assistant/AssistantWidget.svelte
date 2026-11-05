<script lang="ts">
	import { page } from '$app/state';
	import { tick } from 'svelte';
	import { errorMessage, type SessionUser } from '../api';
	import { renderMarkdown } from '../markdown';
	import { detectAssistantContext, type AssistantMessage } from './types';

	let { user }: { user: SessionUser } = $props();

	let isOpen = $state(false);
	let loadedHistory = $state(false);
	let loading = $state(false);
	let clearing = $state(false);
	let question = $state('');
	let errorText = $state<string | null>(null);
	let messages = $state<AssistantMessage[]>([]);

	let triggerEl: HTMLButtonElement | undefined = $state();
	let dialogEl: HTMLDialogElement | undefined = $state();
	let inputEl: HTMLTextAreaElement | undefined = $state();
	let logEl: HTMLDivElement | undefined = $state();

	const contextHint = $derived(detectAssistantContext(page.url.pathname, page.params));
	const orderedMessages = $derived([...messages].reverse());

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

	async function fetchHistory(): Promise<void> {
		if (loadedHistory) return;
		try {
			const res = await fetch('/assistant/history');
			if (res.ok) {
				messages = (await res.json()) as AssistantMessage[];
				loadedHistory = true;
				await scrollLogToBottom();
			}
		} catch {
			// Mantiene estado silencioso al abrir si la red falla temporalmente.
		}
	}

	async function openPanel(): Promise<void> {
		if (!dialogEl) return;
		isOpen = true;
		showNativePanel(dialogEl);
		await tick();
		inputEl?.focus();
		await fetchHistory();
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

	function onDialogKeydown(event: KeyboardEvent): void {
		if (event.key === 'Escape' && isOpen) {
			event.preventDefault();
			closePanel();
		}
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
			messages = [parsed as AssistantMessage, ...messages];
			loadedHistory = true;
			question = '';
			await scrollLogToBottom();
		} catch {
			errorText = 'Error de conexión al consultar al asistente.';
		} finally {
			loading = false;
		}
	}

	async function clearHistory(): Promise<void> {
		if (clearing || messages.length === 0) return;
		clearing = true;
		errorText = null;
		try {
			const res = await fetch('/assistant/history', { method: 'DELETE' });
			if (res.ok) {
				messages = [];
			} else {
				errorText = 'No se pudo limpiar el historial.';
			}
		} catch {
			errorText = 'Error de conexión al limpiar el historial.';
		} finally {
			clearing = false;
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
				<h2 id="assistant-panel-title">Asistente UNSA · PIMS</h2>
				<p class="assistant-ctx" data-testid="assistant-context-label">
					{contextHint.label} · {user.full_name}
				</p>
			</div>
			<div class="assistant-actions">
				<button
					type="button"
					class="btn-secondary"
					disabled={loading || clearing || messages.length === 0}
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

		<!-- svelte-ignore a11y_no_noninteractive_tabindex -->
		<div
			class="assistant-log"
			bind:this={logEl}
			role="log"
			aria-live="polite"
			aria-label="Historial de consultas al asistente"
			tabindex="0"
			data-testid="assistant-log"
		>
			{#if orderedMessages.length === 0}
				<p class="empty-hint">
					Pregúntame sobre ISO/IEC 27701, criterios de auditoría o la estructura ficticia de la UNSA.
					No entrego respuestas exactas de los ejercicios evaluados.
				</p>
				<div class="chips" aria-label="Consultas sugeridas">
					{#each contextHint.suggestions as suggestion (suggestion)}
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
							<p class="msg-question"><strong>Tú:</strong> {msg.question}</p>
							{#if msg.status === 'ok' && msg.answer}
								<div class="msg-answer">
									<!-- eslint-disable-next-line svelte/no-at-html-tags -- Markdown sanitizado -->
									{@html renderMarkdown(msg.answer)}
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

		{#if loading}
			<p class="status-note" role="status" data-testid="assistant-loading">
				Consultando al asistente…
			</p>
		{/if}
		{#if errorText}
			<p class="error-note" role="alert" data-testid="assistant-error">{errorText}</p>
		{/if}

		<form class="assistant-form" onsubmit={handleSubmit}>
			<label for="assistant-question" class="field-label">Tu consulta</label>
			<div class="composer-row">
				<textarea
					id="assistant-question"
					bind:this={inputEl}
					bind:value={question}
					rows="2"
					maxlength={800}
					placeholder="Ej. ¿Qué unidades UNSA intervienen en este proceso?"
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
	.chip-btn:focus-visible,
	.btn-send:focus-visible,
	textarea:focus-visible {
		outline: 3px solid #0b3a75;
		outline-offset: 2px;
	}

	.assistant-panel {
		position: fixed;
		inset: auto 20px 76px auto;
		margin: 0;
		padding: 0;
		width: min(430px, calc(100vw - 24px));
		max-height: min(74vh, 580px);
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
		font-size: 0.8rem;
		color: #465162;
	}

	.assistant-actions {
		display: flex;
		gap: 6px;
		flex-shrink: 0;
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

	.assistant-log {
		flex: 1;
		overflow-y: auto;
		padding: 12px 14px;
		min-height: 180px;
	}

	.empty-hint {
		margin: 0 0 10px;
		font-size: 0.88rem;
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
		font-size: 0.84rem;
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
		font-size: 0.88rem;
	}

	.msg-answer {
		background: var(--surface);
		border: 1px solid var(--border);
		border-radius: 8px;
		padding: 8px 10px;
		font-size: 0.88rem;
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
		font-size: 0.86rem;
	}

	.msg-err {
		margin: 0;
		background: #fff4f2;
		color: #9e1c13;
		border: 1px solid #e0a19c;
		border-radius: 8px;
		padding: 8px 10px;
		font-size: 0.86rem;
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
		font-size: 0.88rem;
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
		font-size: 0.88rem;
		font-weight: 600;
		cursor: pointer;
	}

	.btn-send:disabled {
		opacity: 0.55;
		cursor: not-allowed;
	}
</style>
