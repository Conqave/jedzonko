import { beforeEach, describe, expect, it, vi } from 'vitest';
import { fetchDeletedHouseholds, fetchHouseholds } from './api';

const get = vi.hoisted(() => vi.fn());

vi.mock('@/shared/http', () => ({ http: { get } }));

beforeEach(() => {
  get.mockReset();
});

describe('households api', () => {
  it('maps households to the model', async () => {
    get.mockResolvedValue({ data: [{ id: 1, name: 'Dom', member_count: 2 }] });

    await expect(fetchHouseholds()).resolves.toEqual([{ id: 1, name: 'Dom', memberCount: 2 }]);
  });

  it('parses the recovery window of deleted households', async () => {
    const deleted = {
      id: 1,
      name: 'Dom',
      member_count: 2,
      deleted_at: '2026-09-28T10:00:00+02:00',
      purge_after: '2026-10-28T10:00:00+01:00',
    };
    get.mockResolvedValue({ data: [deleted] });

    const [household] = await fetchDeletedHouseholds();

    expect(household?.purgeAfter.toISOString()).toBe('2026-10-28T09:00:00.000Z');
  });

  it('rejects a response that breaks the contract', async () => {
    get.mockResolvedValue({ data: [{ id: '1', name: 'Dom' }] });

    await expect(fetchHouseholds()).rejects.toThrow();
  });
});
