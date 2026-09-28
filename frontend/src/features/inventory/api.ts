import { http as api } from '@/shared/http';
import type {
  InventoryCategory,
  InventoryItem,
  InventoryItemUpdate,
  NewInventoryItem,
} from './models';

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

export async function updateInventoryItem(
  itemId: number,
  changes: InventoryItemUpdate,
): Promise<InventoryItem> {
  const response = await api.patch<InventoryItem>(`/inventory/${itemId}/`, changes);
  return response.data;
}

export async function deleteInventoryItem(itemId: number): Promise<void> {
  await api.delete(`/inventory/${itemId}/`);
}

export async function fetchInventoryCategories(householdId: number): Promise<InventoryCategory[]> {
  const response = await api.get<InventoryCategory[]>('/inventory/categories/', {
    params: { household_id: householdId },
  });
  return response.data;
}

export async function createInventoryCategory(
  householdId: number,
  name: string,
): Promise<InventoryCategory> {
  const response = await api.post<InventoryCategory>('/inventory/categories/', {
    household_id: householdId,
    name,
  });
  return response.data;
}

export async function setInventoryItemCategory(
  itemId: number,
  categoryId: number | null,
): Promise<InventoryItem> {
  const response = await api.put<InventoryItem>(`/inventory/${itemId}/category/`, {
    category_id: categoryId,
  });
  return response.data;
}

export async function uploadInventoryItemPhoto(
  itemId: number,
  photo: File,
): Promise<InventoryItem> {
  const payload = new FormData();
  payload.append('photo', photo);
  const response = await api.put<InventoryItem>(`/inventory/${itemId}/photo/`, payload);
  return response.data;
}

export async function deleteInventoryItemPhoto(itemId: number): Promise<InventoryItem> {
  const response = await api.delete<InventoryItem>(`/inventory/${itemId}/photo/`);
  return response.data;
}
