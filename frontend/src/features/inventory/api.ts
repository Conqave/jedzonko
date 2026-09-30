import { z } from 'zod';
import { ITEM_UNCOUNTED_REASONS, toItemCalories } from '@/shared/calories';
import { http } from '@/shared/http';
import type { InventoryItem, InventoryItemChanges, NewInventoryItem } from './model';

const caloriesSchema = z
  .object({
    kcal: z.string().nullable(),
    kcal_per_100g: z.string().nullable(),
    is_estimate: z.boolean(),
    uncounted_reason: z.enum(ITEM_UNCOUNTED_REASONS).nullable(),
  })
  .transform(toItemCalories);

const itemSchema = z
  .object({
    id: z.number().int(),
    product_id: z.number().int(),
    product_name: z.string(),
    quantity: z.string(),
    unit_code: z.string(),
    minimum_quantity: z.string().nullable(),
    photo_url: z.string().nullable(),
    below_minimum: z.boolean(),
    calories: caloriesSchema,
  })
  .transform((item): InventoryItem => ({
    id: item.id,
    productId: item.product_id,
    productName: item.product_name,
    quantity: item.quantity,
    unitCode: item.unit_code,
    minimumQuantity: item.minimum_quantity,
    photoUrl: item.photo_url,
    isBelowMinimum: item.below_minimum,
    calories: item.calories,
  }));

export async function fetchInventory(householdId: number): Promise<InventoryItem[]> {
  const params = { household_id: householdId };
  const response = await http.get('/inventory/', { params });
  return itemSchema.array().parse(response.data);
}

export async function addInventoryItem(item: NewInventoryItem): Promise<InventoryItem> {
  const payload = {
    household_id: item.householdId,
    product_id: item.productId,
    quantity: item.quantity,
    unit_code: item.unitCode,
    minimum_quantity: item.minimumQuantity,
  };
  const response = await http.post('/inventory/', payload);
  return itemSchema.parse(response.data);
}

export async function updateInventoryItem(
  itemId: number,
  changes: Partial<InventoryItemChanges>,
): Promise<InventoryItem> {
  const payload = {
    quantity: changes.quantity,
    unit_code: changes.unitCode,
  };
  const response = await http.patch(`/inventory/${itemId}/`, payload);
  return itemSchema.parse(response.data);
}

export async function deleteInventoryItem(itemId: number): Promise<void> {
  await http.delete(`/inventory/${itemId}/`);
}

export async function setInventoryItemMinimum(
  itemId: number,
  minimumQuantity: string | null,
): Promise<InventoryItem> {
  const payload = { minimum_quantity: minimumQuantity };
  const response = await http.put(`/inventory/${itemId}/minimum/`, payload);
  return itemSchema.parse(response.data);
}

export async function uploadInventoryItemPhoto(
  itemId: number,
  photo: File,
): Promise<InventoryItem> {
  const payload = new FormData();
  payload.append('photo', photo);
  const response = await http.put(`/inventory/${itemId}/photo/`, payload);
  return itemSchema.parse(response.data);
}

export async function deleteInventoryItemPhoto(itemId: number): Promise<InventoryItem> {
  const response = await http.delete(`/inventory/${itemId}/photo/`);
  return itemSchema.parse(response.data);
}
