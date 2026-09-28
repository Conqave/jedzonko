import { ref } from 'vue';
import { useApiAction } from '@/shared/useApiAction';
import { fetchDeletedHouseholds } from './api';
import { HOUSEHOLD_ERROR_MESSAGES } from './errors';
import type { DeletedHousehold } from './model';
import { useHouseholdStore } from './store';

export function useDeletedHouseholds() {
  const households = useHouseholdStore();
  const deleted = ref<DeletedHousehold[]>([]);
  const { busy, run } = useApiAction(HOUSEHOLD_ERROR_MESSAGES);

  async function load(): Promise<void> {
    await run(async () => {
      deleted.value = await fetchDeletedHouseholds();
    });
  }

  async function restore(householdId: number): Promise<void> {
    await run(async () => {
      await households.restore(householdId);
      deleted.value = deleted.value.filter((household) => household.id !== householdId);
    });
  }

  return { deleted, busy, load, restore };
}
