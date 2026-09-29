import { computed, ref, watch, type Ref } from 'vue';
import { useApiAction } from '@/shared/useApiAction';
import {
  addInventoryItem,
  deleteInventoryItem,
  deleteInventoryItemPhoto,
  fetchInventory,
  setInventoryItemMinimum,
  updateInventoryItem,
  uploadInventoryItemPhoto,
} from './api';
import { INVENTORY_ERROR_MESSAGES } from './errors';
import type {
  InventoryItem,
  InventoryItemChanges,
  InventoryItemEdit,
  NewInventoryEntry,
} from './model';

export function useInventory(householdId: Ref<number | null>) {
  const items = ref<InventoryItem[]>([]);
  const savingItemId = ref<number | null>(null);
  const { busy, run } = useApiAction(INVENTORY_ERROR_MESSAGES);

  const belowMinimumItems = computed(() => items.value.filter((item) => item.isBelowMinimum));

  function replaceItem(updated: InventoryItem): void {
    items.value = items.value.map((item) => (item.id === updated.id ? updated : item));
  }

  async function load(): Promise<void> {
    const id = householdId.value;
    items.value = [];
    if (id === null) {
      return;
    }
    await run(reload);
  }

  async function reload(): Promise<void> {
    const id = householdId.value;
    if (id === null) {
      return;
    }
    items.value = await fetchInventory(id);
  }

  function add(entry: NewInventoryEntry): Promise<boolean> {
    return run(async () => {
      const added = await addInventoryItem(entry.item);
      items.value = [...items.value, added];
      if (entry.photo !== null) {
        const withPhoto = await uploadInventoryItemPhoto(added.id, entry.photo);
        replaceItem(withPhoto);
      }
    });
  }

  async function update(itemId: number, changes: Partial<InventoryItemChanges>): Promise<boolean> {
    savingItemId.value = itemId;
    const isUpdated = await run(async () => {
      const updated = await updateInventoryItem(itemId, changes);
      replaceItem(updated);
    });
    savingItemId.value = null;
    return isUpdated;
  }

  async function edit(item: InventoryItem, itemEdit: InventoryItemEdit): Promise<boolean> {
    savingItemId.value = item.id;
    const isEdited = await run(async () => {
      const updated = await updateInventoryItem(item.id, itemEdit.changes);
      replaceItem(updated);
      if (itemEdit.minimumQuantity !== item.minimumQuantity) {
        const withMinimum = await setInventoryItemMinimum(item.id, itemEdit.minimumQuantity);
        replaceItem(withMinimum);
      }
    });
    savingItemId.value = null;
    return isEdited;
  }

  function remove(itemId: number): Promise<boolean> {
    return run(async () => {
      await deleteInventoryItem(itemId);
      items.value = items.value.filter((item) => item.id !== itemId);
    });
  }

  function setPhoto(itemId: number, photo: File): Promise<boolean> {
    return run(async () => {
      const updated = await uploadInventoryItemPhoto(itemId, photo);
      replaceItem(updated);
    });
  }

  function removePhoto(itemId: number): Promise<boolean> {
    return run(async () => {
      const updated = await deleteInventoryItemPhoto(itemId);
      replaceItem(updated);
    });
  }

  watch(householdId, load, { immediate: true });

  return {
    load,
    items,
    belowMinimumItems,
    busy,
    savingItemId,
    add,
    update,
    edit,
    remove,
    setPhoto,
    removePhoto,
  };
}
