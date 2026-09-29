import { computed, ref, watch, type Ref } from 'vue';
import { useApiAction } from '@/shared/useApiAction';
import {
  addShoppingItem,
  buyShoppingItems,
  chooseShoppingItemProduct,
  deleteShoppingItem,
  fetchShoppingItems,
  restoreShoppingItem,
} from './api';
import { SHOPPING_ERROR_MESSAGES } from './errors';
import type { NewShoppingItem, ShoppingItem } from './model';

export function useShoppingItems(listId: Ref<number | null>) {
  const items = ref<ShoppingItem[]>([]);
  const { busy, run } = useApiAction(SHOPPING_ERROR_MESSAGES);

  const pendingItems = computed(() => items.value.filter((item) => item.status === 'pending'));
  const purchasedItems = computed(() => items.value.filter((item) => item.status === 'purchased'));

  async function reload(id: number): Promise<void> {
    items.value = await fetchShoppingItems(id);
  }

  async function load(): Promise<void> {
    const id = listId.value;
    items.value = [];
    if (id === null) {
      return;
    }
    await run(() => reload(id));
  }

  function add(item: NewShoppingItem): Promise<boolean> {
    const id = listId.value;
    if (id === null) {
      return Promise.resolve(false);
    }
    return run(async () => {
      await addShoppingItem(id, item);
      await reload(id);
    });
  }

  function buy(itemIds: number[]): Promise<boolean> {
    const id = listId.value;
    if (id === null || itemIds.length === 0) {
      return Promise.resolve(false);
    }
    return run(async () => {
      await buyShoppingItems(id, itemIds);
      await reload(id);
    });
  }

  function restore(item: ShoppingItem): Promise<boolean> {
    return run(async () => {
      await restoreShoppingItem(item.id);
      await reload(item.listId);
    });
  }

  function chooseProduct(item: ShoppingItem, productId: number): Promise<boolean> {
    return run(async () => {
      await chooseShoppingItemProduct(item.id, productId);
      await reload(item.listId);
    });
  }

  function remove(item: ShoppingItem): Promise<boolean> {
    return run(async () => {
      await deleteShoppingItem(item.id);
      items.value = items.value.filter((entry) => entry.id !== item.id);
    });
  }

  watch(listId, load, { immediate: true });

  return {
    items,
    pendingItems,
    purchasedItems,
    busy,
    load,
    add,
    buy,
    restore,
    chooseProduct,
    remove,
  };
}
