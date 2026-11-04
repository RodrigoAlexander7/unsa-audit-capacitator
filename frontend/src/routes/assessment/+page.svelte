<script lang="ts">
	import { PROFILE_LABEL, type AssessmentProfile } from '../../lib/api';
	import { formatDate } from '../../lib/format';
	import type { PageProps } from './$types';

	let { data, form }: PageProps = $props();

	const PROFILES: { id: AssessmentProfile; text: string }[] = [
		{
			id: 'controller',
			text: 'Decides para qué y cómo se tratan los datos personales: finalidad, derechos de los titulares, contratos con encargados, brechas y transferencias.'
		},
		{
			id: 'processor',
			text: 'Tratas datos por cuenta de otro: instrucciones documentadas, subencargados, asistencia al responsable, brechas y supresión de datos.'
		}
	];
</script>

<h1>Evaluación para controller y processor</h1>
<p class="lead">
	12 preguntas por perfil. Verás tu puntaje por competencia y por requisito del PIMS para saber qué
	reforzar. Apruebas con 70 % o más y puedes repetirla cuantas veces quieras.
</p>

{#if form?.error}<p class="error" role="alert">{form.error}</p>{/if}

<div class="grid">
	{#each PROFILES as profile (profile.id)}
		<form method="POST" class="card" data-testid={`profile-${profile.id}`}>
			<h2>{PROFILE_LABEL[profile.id]}</h2>
			<p class="muted">{profile.text}</p>
			<input type="hidden" name="profile" value={profile.id} />
			<button type="submit">Iniciar evaluación</button>
		</form>
	{/each}
</div>

<h2>Mis evaluaciones</h2>
{#if data.attempts.length}
	<div class="card table-card">
		<table data-testid="attempts-table">
			<thead>
				<tr><th>Fecha</th><th>Perfil</th><th>Estado</th><th>Puntaje</th><th></th></tr>
			</thead>
			<tbody>
				{#each data.attempts as attempt (attempt.id)}
					<tr>
						<td>{formatDate(attempt.started_at)}</td>
						<td>{PROFILE_LABEL[attempt.profile]}</td>
						<td>
							{#if attempt.status === 'finished'}
								{attempt.passed ? '✓ Aprobada' : '✗ No aprobada'}
							{:else}
								En curso
							{/if}
						</td>
						<td>{attempt.score !== null ? `${attempt.score} %` : '—'}</td>
						<td>
							<a href={`/assessment/${attempt.id}`}
								>{attempt.status === 'finished' ? 'Ver resultado' : 'Continuar'}</a
							>
						</td>
					</tr>
				{/each}
			</tbody>
		</table>
	</div>
{:else}
	<p class="muted">Aún no has hecho ninguna evaluación.</p>
{/if}

<style>
	.lead,
	.muted {
		color: var(--muted);
		max-width: 65ch;
	}

	.grid {
		display: grid;
		gap: 16px;
		grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
		margin: 16px 0 28px;
	}

	h2 {
		font-size: 1.1rem;
		margin-top: 0;
	}

	.grid h2 {
		margin-bottom: 6px;
	}

	button {
		background: var(--primary);
		color: var(--primary-contrast);
		border: none;
		border-radius: 8px;
		padding: 10px 16px;
		font: inherit;
		cursor: pointer;
	}

	.table-card {
		padding: 0;
		overflow-x: auto;
	}

	table {
		width: 100%;
		border-collapse: collapse;
		font-size: 0.93rem;
	}

	th,
	td {
		text-align: left;
		padding: 10px 14px;
		border-bottom: 1px solid var(--border);
	}

	th {
		color: var(--muted);
		font-size: 0.8rem;
		font-weight: 600;
	}

	tr:last-child td {
		border-bottom: none;
	}

	.error {
		color: var(--danger);
	}
</style>
