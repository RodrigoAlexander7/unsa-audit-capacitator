// See https://svelte.dev/docs/kit/types#app.d.ts
// for information about these interfaces
import type { SessionUser } from './lib/api';

declare global {
	namespace App {
		// interface Error {}
		interface Locals {
			user: SessionUser | null;
			token: string | null;
		}
		// interface PageData {}
		// interface PageState {}
		// interface Platform {}
	}
}

export {};
