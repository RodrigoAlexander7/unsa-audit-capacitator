<script lang="ts">
	import type { ItemFeedback } from './types';

	let {
		feedback = undefined,
		id = undefined
	}: {
		feedback?: ItemFeedback | undefined;
		id?: string | undefined;
	} = $props();
</script>

{#if feedback}
	<p
		{id}
		class="doc-fb"
		class:ok={feedback.correct}
		class:bad={!feedback.correct}
		role={feedback.correct ? 'status' : 'alert'}
	>
		<strong>{feedback.correct ? '✓ Correcto' : '✗ Por corregir'}:</strong>
		{feedback.feedback}
	</p>
{/if}
