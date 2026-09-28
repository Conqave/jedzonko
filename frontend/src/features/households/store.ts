import { defineStore } from 'pinia';
import { computed, ref } from 'vue';
import {
  createHousehold,
  deleteHousehold,
  fetchHouseholds,
  renameHousehold,
  restoreHousehold,
} from './api';
import type { Household } from './model';

const SELECTED_HOUSEHOLD_KEY = 'jedzonko.selectedHouseholdId';

function loadSelectedHouseholdId(): number | null {
  const stored = localStorage.getItem(SELECTED_HOUSEHOLD_KEY);
  if (stored === null) {
    return null;
  }
  const parsed = Number(stored);
  return Number.isInteger(parsed) ? parsed : null;
}

function saveSelectedHouseholdId(householdId: number | null): void {
  if (householdId === null) {
    localStorage.removeItem(SELECTED_HOUSEHOLD_KEY);
    return;
  }
  localStorage.setItem(SELECTED_HOUSEHOLD_KEY, String(householdId));
}

export const useHouseholdStore = defineStore('households', () => {
  const households = ref<Household[]>([]);
  const selectedId = ref<number | null>(loadSelectedHouseholdId());
  const isLoaded = ref(false);

  const selected = computed(
    () => households.value.find((household) => household.id === selectedId.value) ?? null,
  );
  const hasHousehold = computed(() => households.value.length > 0);

  function select(householdId: number | null): void {
    selectedId.value = householdId;
    saveSelectedHouseholdId(householdId);
  }

  function selectAvailable(): void {
    const isSelectedAvailable = households.value.some(
      (household) => household.id === selectedId.value,
    );
    if (!isSelectedAvailable) {
      select(households.value[0]?.id ?? null);
    }
  }

  async function load(): Promise<void> {
    households.value = await fetchHouseholds();
    selectAvailable();
    isLoaded.value = true;
  }

  async function create(name: string): Promise<void> {
    const household = await createHousehold(name);
    households.value = [...households.value, household];
    select(household.id);
  }

  async function rename(householdId: number, name: string): Promise<void> {
    const renamed = await renameHousehold(householdId, name);
    households.value = households.value.map((household) =>
      household.id === renamed.id ? renamed : household,
    );
  }

  async function remove(householdId: number): Promise<void> {
    await deleteHousehold(householdId);
    households.value = households.value.filter((household) => household.id !== householdId);
    selectAvailable();
  }

  async function restore(householdId: number): Promise<void> {
    const restored = await restoreHousehold(householdId);
    households.value = [...households.value, restored];
    selectAvailable();
  }

  function refreshMemberCount(householdId: number, memberCount: number): void {
    households.value = households.value.map((household) =>
      household.id === householdId ? { ...household, memberCount } : household,
    );
  }

  return {
    households,
    selectedId,
    selected,
    hasHousehold,
    isLoaded,
    select,
    load,
    create,
    rename,
    remove,
    restore,
    refreshMemberCount,
  };
});
