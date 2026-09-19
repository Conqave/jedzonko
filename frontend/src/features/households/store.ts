import { defineStore } from 'pinia';
import { computed, ref } from 'vue';
import * as householdsApi from './api';
import type { Household } from './models';

const SELECTED_HOUSEHOLD_KEY = 'jedzonko.selectedHouseholdId';

function readStoredHouseholdId(): number | null {
  const stored = localStorage.getItem(SELECTED_HOUSEHOLD_KEY);
  if (stored === null) {
    return null;
  }
  const parsed = Number.parseInt(stored, 10);
  return Number.isNaN(parsed) ? null : parsed;
}

export const useHouseholdStore = defineStore('households', () => {
  const households = ref<Household[]>([]);
  const selectedId = ref<number | null>(readStoredHouseholdId());
  const loading = ref(false);
  const loaded = ref(false);

  const selected = computed(
    () => households.value.find((household) => household.id === selectedId.value) ?? null,
  );
  const hasHousehold = computed(() => households.value.length > 0);

  function select(householdId: number | null): void {
    selectedId.value = householdId;
    if (householdId === null) {
      localStorage.removeItem(SELECTED_HOUSEHOLD_KEY);
    } else {
      localStorage.setItem(SELECTED_HOUSEHOLD_KEY, String(householdId));
    }
  }

  async function load(): Promise<void> {
    loading.value = true;
    try {
      households.value = await householdsApi.fetchHouseholds();
      const current = households.value.find((household) => household.id === selectedId.value);
      if (current === undefined) {
        select(households.value[0]?.id ?? null);
      }
      loaded.value = true;
    } finally {
      loading.value = false;
    }
  }

  async function create(name: string): Promise<Household> {
    const household = await householdsApi.createHousehold(name);
    households.value = [...households.value, household];
    select(household.id);
    return household;
  }

  async function rename(householdId: number, name: string): Promise<Household> {
    const renamed = await householdsApi.renameHousehold(householdId, name);
    households.value = households.value.map((household) =>
      household.id === renamed.id ? renamed : household,
    );
    return renamed;
  }

  return {
    households,
    selectedId,
    selected,
    hasHousehold,
    loading,
    loaded,
    select,
    load,
    create,
    rename,
  };
});
