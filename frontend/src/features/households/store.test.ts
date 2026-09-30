import { createPinia, setActivePinia } from 'pinia';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { deleteHousehold, fetchHouseholds, restoreHousehold } from './api';
import { useHouseholdStore } from './store';

vi.mock('./api', () => ({
  fetchHouseholds: vi.fn(),
  deleteHousehold: vi.fn(),
  createHousehold: vi.fn(),
  renameHousehold: vi.fn(),
  restoreHousehold: vi.fn(),
}));

const HOME = { id: 1, name: 'Dom', memberCount: 2 };
const COTTAGE = { id: 2, name: 'Działka', memberCount: 1 };

beforeEach(() => {
  localStorage.clear();
  setActivePinia(createPinia());
  vi.mocked(fetchHouseholds).mockResolvedValue([HOME, COTTAGE]);
  vi.mocked(deleteHousehold).mockResolvedValue();
});

describe('household store', () => {
  it('selects the first household when none was chosen', async () => {
    const store = useHouseholdStore();

    await store.load();

    expect(store.selected).toEqual(HOME);
  });

  it('keeps the remembered household', async () => {
    localStorage.setItem('jedzonko.selectedHouseholdId', '2');
    const store = useHouseholdStore();

    await store.load();

    expect(store.selected).toEqual(COTTAGE);
  });

  it('moves the selection when the selected household is deleted', async () => {
    const store = useHouseholdStore();
    await store.load();

    await store.remove(HOME.id);

    expect(store.selected).toEqual(COTTAGE);
    expect(localStorage.getItem('jedzonko.selectedHouseholdId')).toBe('2');
  });

  it('shows a restored household where the server lists it', async () => {
    vi.mocked(fetchHouseholds).mockResolvedValueOnce([COTTAGE]);
    vi.mocked(restoreHousehold).mockResolvedValue(HOME);
    const store = useHouseholdStore();
    await store.load();

    await store.restore(HOME.id);

    expect(store.households).toEqual([HOME, COTTAGE]);
    expect(store.selected).toEqual(COTTAGE);
  });
});
