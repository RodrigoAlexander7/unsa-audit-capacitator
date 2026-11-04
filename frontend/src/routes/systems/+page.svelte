<script lang="ts">
	import { ROLE_LABEL } from '../../lib/api';
	import type { PageProps } from './$types';

	let { data }: PageProps = $props();
</script>

<h1>Sistemas y dueños de datos</h1>
<p class="lead">¿Qué sistemas usa la UNSA (ficticia), quién los gobierna y qué datos manejan?</p>

<div class="grid">
	{#each data.systems as s (s.id)}
		<article class="card">
			<h2>{s.name}</h2>
			<p class="muted">{s.description}</p>
			<p>
				<strong>Unidad:</strong>
				<a href={`/university/${s.owner_unit.id}`}>{s.owner_unit.name}</a>
			</p>
			<p>
				<strong>Datos:</strong>
				{#each s.data_categories as cat (cat)}<span class="chip">{cat}</span>{/each}
			</p>
			<ul>
				{#each s.owners as o (o.person.id + o.role)}
					<li>{ROLE_LABEL[o.role] ?? o.role}: {o.person.full_name}</li>
				{/each}
			</ul>
		</article>
	{:else}
		<p class="card">No hay sistemas cargados. Ejecuta el seed del backend.</p>
	{/each}
</div>

<style>
	.lead,
	.muted {
		color: var(--muted);
	}

	.grid {
		display: grid;
		gap: 16px;
		grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
	}

	h2 {
		margin-top: 0;
		font-size: 1.1rem;
	}

	.chip {
		display: inline-block;
		background: var(--bg);
		border: 1px solid var(--border);
		border-radius: 999px;
		padding: 1px 9px;
		margin: 0 4px 4px 0;
		font-size: 0.8rem;
	}

	ul {
		margin: 0;
		padding-left: 1.1rem;
		font-size: 0.9rem;
	}
</style>
