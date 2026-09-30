import { ref, watch, type Ref } from 'vue';
import { useApiAction } from '@/shared/useApiAction';
import { addMember, fetchMembers, removeMember } from './api';
import { HOUSEHOLD_ERROR_MESSAGES } from './errors';
import type { HouseholdMember } from './model';

export function useHouseholdMembers(householdId: Ref<number | null>) {
  const members = ref<HouseholdMember[]>([]);
  const { busy, run } = useApiAction(HOUSEHOLD_ERROR_MESSAGES);

  async function load(): Promise<void> {
    const id = householdId.value;
    members.value = [];
    if (id === null) {
      return;
    }
    await run(async () => {
      members.value = await fetchMembers(id);
    });
  }

  function add(id: number, username: string): Promise<boolean> {
    return run(async () => {
      const member = await addMember(id, username);
      members.value = [...members.value, member];
    });
  }

  function remove(id: number, member: HouseholdMember): Promise<boolean> {
    return run(async () => {
      await removeMember(id, member.userId);
      members.value = members.value.filter((entry) => entry.userId !== member.userId);
    });
  }

  watch(householdId, load, { immediate: true });

  return { members, busy, add, remove };
}
