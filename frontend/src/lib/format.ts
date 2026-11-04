/** Fecha legible en español. Se fija UTC para que servidor y navegador rindan lo mismo. */
export function formatDate(iso: string): string {
	return new Date(iso).toLocaleDateString('es-PE', {
		timeZone: 'UTC',
		day: '2-digit',
		month: 'short',
		year: 'numeric'
	});
}
