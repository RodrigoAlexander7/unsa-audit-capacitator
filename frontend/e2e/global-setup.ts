import { execFileSync } from 'node:child_process';
import { resolve } from 'node:path';

/** Garantiza el seed base + cohorte demo (idempotente) antes de la suite. */
export default function globalSetup(): void {
	const backend = resolve(import.meta.dirname, '../../backend');
	execFileSync('uv', ['run', 'python', '-m', 'unsa_audit.seed', '--demo'], {
		cwd: backend,
		stdio: 'inherit'
	});
}
