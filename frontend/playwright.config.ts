import { defineConfig } from '@playwright/test';

const WEB_PORT = 5173;
const API_PORT = 8000;

// Requiere Postgres levantado y migrado (`./dev.sh` lo hace). El seed demo lo carga global-setup.
export default defineConfig({
	testDir: './e2e',
	globalSetup: './e2e/global-setup.ts',
	timeout: 60_000,
	expect: { timeout: 10_000 },
	fullyParallel: false,
	workers: 1,
	reporter: [['list']],
	use: {
		baseURL: `http://localhost:${WEB_PORT}`,
		// Usa el Chrome del sistema: no hace falta descargar navegadores de Playwright.
		channel: 'chrome',
		trace: 'retain-on-failure'
	},
	webServer: [
		{
			command: `uv run uvicorn unsa_audit.main:app --port ${API_PORT}`,
			cwd: '../backend',
			url: `http://localhost:${API_PORT}/health`,
			reuseExistingServer: true,
			timeout: 60_000
		},
		{
			command: `npm run dev -- --port ${WEB_PORT} --strictPort`,
			url: `http://localhost:${WEB_PORT}/login`,
			reuseExistingServer: true,
			timeout: 60_000
		}
	]
});
