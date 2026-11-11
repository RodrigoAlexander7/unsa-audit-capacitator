<script lang="ts">
	import type { PageProps } from './$types';

	let { form }: PageProps = $props();
</script>

<h1>Crear cuenta</h1>

<form method="POST" class="card form">
	{#if form?.error}<p class="error" role="alert" data-testid="form-error">{form.error}</p>{/if}
	<label>
		Nombre completo
		<input type="text" name="full_name" value={form?.full_name ?? ''} autocomplete="name" required maxlength="120" />
	</label>
	<label>
		Correo electrónico
		<input type="email" name="email" value={form?.email ?? ''} autocomplete="email" required />
	</label>
	<label>
		Contraseña (mínimo 8 caracteres)
		<input type="password" name="password" autocomplete="new-password" minlength="8" required />
	</label>
	<button type="submit">Registrarme</button>
	<p class="alt">¿Ya tienes cuenta? <a href="/login">Inicia sesión</a></p>
</form>

<style>
	.form {
		max-width: 420px;
		display: grid;
		gap: 14px;
	}

	label {
		display: grid;
		gap: 4px;
		font-size: 0.9rem;
	}

	input {
		padding: 9px 10px;
		border: 1px solid var(--border);
		border-radius: 8px;
		font: inherit;
	}

	button {
		background: var(--primary);
		color: var(--primary-contrast);
		border: none;
		border-radius: 8px;
		padding: 10px 14px;
		font: inherit;
		cursor: pointer;
	}

	.error {
		color: var(--danger);
		margin: 0;
	}

	.alt {
		margin: 0;
		color: var(--muted);
		font-size: 0.9rem;
	}
</style>
