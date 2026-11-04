<script lang="ts">
	import { KIND_LABEL, type OrgTree } from '../../lib/api';
	import type { PageProps } from './$types';

	let { data }: PageProps = $props();
</script>

<h1>La universidad</h1>
<p class="lead">
	Organigrama de la UNSA (ficticia). Entra en cada unidad para ver sus cargos y quién los ocupa.
</p>

{#snippet branch(node: OrgTree)}
	<li>
		<a href={`/university/${node.id}`}>{node.name}</a>
		<span class="kind">{KIND_LABEL[node.kind] ?? node.kind}</span>
		{#if node.children.length}
			<ul>
				{#each node.children as child (child.id)}
					{@render branch(child)}
				{/each}
			</ul>
		{/if}
	</li>
{/snippet}

{#if data.tree}
	<section class="card tree" aria-label="Organigrama">
		<ul class="root">
			{@render branch(data.tree)}
		</ul>
	</section>
{:else}
	<p class="card">No hay organigrama cargado. Ejecuta el seed del backend.</p>
{/if}

<style>
	.lead {
		color: var(--muted);
		max-width: 60ch;
	}

	ul {
		list-style: none;
		margin: 0;
		padding-left: 1.4rem;
		border-left: 1px solid var(--border);
	}

	ul.root {
		padding-left: 0;
		border-left: none;
	}

	li {
		padding: 3px 0;
	}

	.kind {
		margin-left: 8px;
		font-size: 0.75rem;
		color: var(--muted);
		background: var(--bg);
		border: 1px solid var(--border);
		border-radius: 999px;
		padding: 1px 8px;
	}
</style>
