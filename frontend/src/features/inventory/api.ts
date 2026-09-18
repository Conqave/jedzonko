import { api } from '@/boot/api';
import type { InventoryItem, NewInventoryItem } from './models';

export async function fetchInventory(householdId: number): Promise<InventoryItem[]> {
  const response = await api.get<InventoryItem[]>('/inventory/', {
    params: { household_id: householdId },
  });
  return response.data;
}

export async function addInventoryItem(item: NewInventoryItem): Promise<InventoryItem> {
  const response = await api.post<InventoryItem>('/inventory/', item);
  return response.data;
}

export async function updateInventoryQuantity(
  itemId: number,
  quantity: string,
): Promise<InventoryItem> {
  const response = await api.patch<InventoryItem>(`/inventory/${itemId}/`, { quantity });
  return response.data;
}

export async function deleteInventoryItem(itemId: number): Promise<void> {
  await api.delete(`/inventory/${itemId}/`);
}
