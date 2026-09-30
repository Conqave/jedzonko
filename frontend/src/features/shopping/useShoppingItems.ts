import { ref, watch, type Ref } from 'vue';
import { useApiAction } from '@/shared/useApiAction';
import {
  addShoppingItem,
  buyShoppingItems,
  chooseShoppingItemProduct,
  deleteShoppingItem,
  deleteShoppingItems,
  fetchShoppingItems,
  interpretShoppingItem,
  restoreShoppingItem,
  tagShoppingItem,
  tagShoppingList,
} from './api';
import { SHOPPING_ERROR_MESSAGES } from './errors';
import type {
  NewShoppingItem,
  ShoppingItem,
  ShoppingItemInterpretation,
  ShoppingItemTagging,
  ShoppingPurchase,
} from './model';

export function useShoppingItems(listId: Ref<number | null>) {
  const items = ref<ShoppingItem[]>([]);
  const { busy, run } = useApiAction(SHOPPING_ERROR_MESSAGES);

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

  function buy(purchases: ShoppingPurchase[]): Promise<boolean> {
    const id = listId.value;
    if (id === null || purchases.length === 0) {
      return Promise.resolve(false);
    }
    return run(async () => {
      await buyShoppingItems(id, purchases);
      await reload(id);
    });
  }

  function restore(item: ShoppingItem): Promise<boolean> {
    return run(async () => {
      await restoreShoppingItem(item.id);
      await reload(item.listId);
    });
  }

  const isTagging = ref(false);

  async function tagList(): Promise<boolean> {
    const id = listId.value;
    if (id === null) {
      return false;
    }
    isTagging.value = true;
    const isTagged = await run(async () => {
      items.value = await tagShoppingList(id);
    });
    isTagging.value = false;
    return isTagged;
  }

  function chooseProduct(item: ShoppingItem, productId: number): Promise<boolean> {
    return run(async () => {
      await chooseShoppingItemProduct(item.id, productId);
      await reload(item.listId);
    });
  }

  function tagItem(
    item: ShoppingItem,
    tagging: ShoppingItemTagging,
    productId: number | null,
  ): Promise<boolean> {
    return run(async () => {
      const tagged = await tagShoppingItem(item.id, tagging);
      if (productId !== null) {
        await chooseShoppingItemProduct(tagged.id, productId);
      }
      await reload(item.listId);
    });
  }

  async function interpretItem(item: ShoppingItem): Promise<ShoppingItemInterpretation | null> {
    const interpretation = ref<ShoppingItemInterpretation | null>(null);
    await run(async () => {
      interpretation.value = await interpretShoppingItem(item.id);
    });
    return interpretation.value;
  }

  function remove(item: ShoppingItem): Promise<boolean> {
    return run(async () => {
      await deleteShoppingItem(item.id);
      items.value = items.value.filter((entry) => entry.id !== item.id);
    });
  }

  function removeMany(removed: ShoppingItem[]): Promise<boolean> {
    const id = listId.value;
    if (id === null || removed.length === 0) {
      return Promise.resolve(false);
    }
    const removedIds = new Set(removed.map((item) => item.id));
    return run(async () => {
      await deleteShoppingItems(id, [...removedIds]);
      items.value = items.value.filter((entry) => !removedIds.has(entry.id));
    });
  }

  watch(listId, load, { immediate: true });

  return {
    items,
    busy,
    load,
    add,
    buy,
    restore,
    chooseProduct,
    tagList,
    isTagging,
    tagItem,
    interpretItem,
    remove,
    removeMany,
  };
}
