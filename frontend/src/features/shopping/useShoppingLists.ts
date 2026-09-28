import { computed, ref, watch, type Ref } from 'vue';
import { useApiAction } from '@/shared/useApiAction';
import {
  createShoppingList,
  deleteShoppingList,
  fetchShoppingLists,
  renameShoppingList,
  splitByPromotions,
  synchronizeMinimumStock,
} from './api';
import { SHOPPING_ERROR_MESSAGES } from './errors';
import { orderPrimaryFirst, type ShoppingList } from './model';

export function useShoppingLists(householdId: Ref<number | null>) {
  const lists = ref<ShoppingList[]>([]);
  const selectedListId = ref<number | null>(null);
  const { busy, run } = useApiAction(SHOPPING_ERROR_MESSAGES);

  const selectedList = computed(
    () => lists.value.find((list) => list.id === selectedListId.value) ?? null,
  );

  function selectAvailable(): void {
    const isSelectedAvailable = lists.value.some((list) => list.id === selectedListId.value);
    if (!isSelectedAvailable) {
      selectedListId.value = lists.value[0]?.id ?? null;
    }
  }

  async function reload(id: number): Promise<void> {
    const found = await fetchShoppingLists(id);
    lists.value = orderPrimaryFirst(found);
    selectAvailable();
  }

  async function load(): Promise<void> {
    const id = householdId.value;
    lists.value = [];
    selectedListId.value = null;
    if (id === null) {
      return;
    }
    await run(() => reload(id));
  }

  function create(name: string): Promise<boolean> {
    const id = householdId.value;
    if (id === null) {
      return Promise.resolve(false);
    }
    return run(async () => {
      const created = await createShoppingList(id, name);
      await reload(id);
      selectedListId.value = created.id;
    });
  }

  function rename(listId: number, name: string): Promise<boolean> {
    return run(async () => {
      const renamed = await renameShoppingList(listId, name);
      lists.value = lists.value.map((list) => (list.id === renamed.id ? renamed : list));
    });
  }

  function remove(listId: number): Promise<boolean> {
    return run(async () => {
      await deleteShoppingList(listId);
      lists.value = lists.value.filter((list) => list.id !== listId);
      selectAvailable();
    });
  }

  function refillMinimumStock(): Promise<boolean> {
    const id = householdId.value;
    if (id === null) {
      return Promise.resolve(false);
    }
    return run(async () => {
      await synchronizeMinimumStock(id);
      await reload(id);
    });
  }

  function splitSelected(shopSlugs: string[]): Promise<boolean> {
    const id = householdId.value;
    const listId = selectedListId.value;
    if (id === null || listId === null) {
      return Promise.resolve(false);
    }
    return run(async () => {
      await splitByPromotions(listId, shopSlugs);
      await reload(id);
    });
  }

  watch(householdId, load, { immediate: true });

  return {
    lists,
    selectedListId,
    selectedList,
    busy,
    load,
    create,
    rename,
    remove,
    refillMinimumStock,
    splitSelected,
  };
}
