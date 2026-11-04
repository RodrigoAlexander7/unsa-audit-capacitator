import { describe, expect, it } from 'vitest';
import { formatDate } from './format';

describe('formatDate', () => {
	it('usa UTC para que no dependa de la zona horaria', () => {
		expect(formatDate('2025-09-15T09:00:00Z')).toMatch(/15/);
		expect(formatDate('2025-09-15T09:00:00Z')).toMatch(/2025/);
		// medianoche UTC sigue siendo el mismo dia
		expect(formatDate('2025-03-10T00:00:00Z')).toMatch(/10/);
	});
});
