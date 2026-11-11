<script lang="ts">
	import { PROFILE_LABEL } from '../../lib/api';
	import type { PageProps } from './$types';

	let { data }: PageProps = $props();
	const totalEnrolled = $derived((data.routes ?? []).reduce((sum, r) => sum + r.enrolled, 0));
</script>

<h1>Panel del superadmin</h1>
<p class="lead">
	Estado de las rutas y de las evaluaciones (solo participantes). Consulta a la IA en el
	<a href="/admin/advisor">asesor</a> para obtener ajustes propuestos al plan de enseñanza.
</p>

{#if data.routes}
	<section class="card" aria-labelledby="rutas">
		<h2 id="rutas">Rutas <span class="meta">({totalEnrolled} matrículas)</span></h2>
		<div class="scroll">
			<table data-testid="routes-table">
				<thead>
					<tr>
						<th>Ruta</th>
						<th>Matriculados</th>
						<th>En curso</th>
						<th>Completados</th>
						<th>Finalización</th>
						<th>Avance medio</th>
						<th>Aprob. intentos</th>
						<th>Estancados*</th>
					</tr>
				</thead>
				<tbody>
					{#each data.routes as route (route.code)}
						<tr data-testid={`stats-${route.code}`}>
							<td><strong>{route.order}. {route.title}</strong></td>
							<td>{route.enrolled}</td>
							<td>{route.in_progress}</td>
							<td>{route.completed}</td>
							<td>{route.completion_rate} %</td>
							<td>
								<progress value={route.avg_progress} max="100"></progress>
								{route.avg_progress} %
							</td>
							<td>{route.attempts ? `${route.pass_rate} % de ${route.attempts}` : '—'}</td>
							<td class:warn={route.stalled > 0}>{route.stalled}</td>
						</tr>
					{/each}
				</tbody>
			</table>
		</div>
		<p class="meta">* Matriculados en curso sin intentos en los últimos 7 días.</p>
	</section>

	<section class="card" aria-labelledby="dificiles">
		<h2 id="dificiles">Módulos más difíciles</h2>
		{#if data.hardest.length}
			<ul class="hard" data-testid="hardest">
				{#each data.hardest as module (module.id)}
					<li>
						<strong>{module.title}</strong>
						<span class="meta">
							{module.route_title} · aprobación {module.pass_rate} % · puntaje medio {module.avg_score} %
							· {module.attempts} intentos
						</span>
					</li>
				{/each}
			</ul>
		{:else}
			<p class="meta">Aún no hay módulos con intentos suficientes (mínimo 3) y aprobación incompleta.</p>
		{/if}
	</section>
{:else}
	<p class="card">No se pudieron cargar las estadísticas.</p>
{/if}

<section class="card" aria-labelledby="eval">
	<h2 id="eval">Evaluaciones controller / processor</h2>
	{#if data.assessments.length}
		<div class="grid">
			{#each data.assessments as profile (profile.profile)}
				<div data-testid={`assessment-${profile.profile}`}>
					<h3>{PROFILE_LABEL[profile.profile]}</h3>
					<p class="meta">
						{profile.finished} enviada(s) · puntaje medio {profile.avg_score} % · aprobación {profile.pass_rate}
						%
					</p>
					<h4>Competencias (peores primero)</h4>
					<ul class="bars">
						{#each profile.competencies as g (g.key)}
							<li>
								<span>{g.label}</span>
								<progress value={g.average} max="100"></progress>
								<span class="pct">{g.average} %</span>
							</li>
						{/each}
					</ul>
					<h4>Requisitos del PIMS (peores primero)</h4>
					<ul class="bars">
						{#each profile.requirements as g (g.key)}
							<li>
								<span>{g.label}</span>
								<progress value={g.average} max="100"></progress>
								<span class="pct">{g.average} %</span>
							</li>
						{/each}
					</ul>
				</div>
			{/each}
		</div>
	{:else}
		<p class="meta">Aún no hay evaluaciones enviadas por participantes.</p>
	{/if}
</section>

{#if data.pims}
	<section class="card" aria-labelledby="pims">
		<h2 id="pims">Conjunto documental del PIMS</h2>
		<p>
			<strong data-testid="pims-summary">{data.pims.in_force} de {data.pims.total} vigentes</strong>
			· borrador {data.pims.counts.draft} · vencidos {data.pims.counts.expired} · sin responsable
			{data.pims.counts.unowned} · inexistentes {data.pims.counts.missing}
			— <a href="/documents/pims">ver matriz</a>
		</p>
	</section>
{/if}

<style>
	.lead,
	.meta {
		color: var(--muted);
	}

	.meta {
		font-size: 0.88rem;
	}

	.card {
		margin: 16px 0;
	}

	h2 {
		margin-top: 0;
		font-size: 1.15rem;
	}

	h3 {
		margin: 0 0 4px;
		font-size: 1rem;
	}

	h4 {
		margin: 14px 0 6px;
		font-size: 0.85rem;
		color: var(--muted);
	}

	.scroll {
		overflow-x: auto;
	}

	table {
		width: 100%;
		border-collapse: collapse;
		font-size: 0.92rem;
	}

	th,
	td {
		text-align: left;
		padding: 8px 10px;
		border-bottom: 1px solid var(--border);
		white-space: nowrap;
	}

	th {
		color: var(--muted);
		font-size: 0.8rem;
		font-weight: 600;
	}

	td.warn {
		color: var(--warn);
		font-weight: 700;
	}

	progress {
		width: 80px;
		height: 8px;
		vertical-align: middle;
	}

	.hard {
		list-style: none;
		margin: 0;
		padding: 0;
		display: grid;
		gap: 8px;
	}

	.hard li {
		display: grid;
	}

	.grid {
		display: grid;
		gap: 24px;
		grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
	}

	.bars {
		list-style: none;
		margin: 0;
		padding: 0;
		display: grid;
		gap: 6px;
		font-size: 0.88rem;
	}

	.bars li {
		display: grid;
		grid-template-columns: minmax(120px, 2fr) 1fr auto;
		gap: 8px;
		align-items: center;
	}

	.bars progress {
		width: 100%;
	}

	.pct {
		color: var(--muted);
		white-space: nowrap;
	}
</style>
