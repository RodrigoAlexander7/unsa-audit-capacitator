import { defineEnvVars } from '@sveltejs/kit/env';

export const variables = defineEnvVars({
	API_URL: {
		description: 'URL base del backend FastAPI (solo servidor).',
		schema: (value) => value ?? 'http://localhost:8000'
	}
});
