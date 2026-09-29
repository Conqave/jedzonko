import { z } from 'zod';
import { http } from '@/shared/http';
import type {
  InventoryCategory,
  InventoryItem,
  InventoryItemChanges,
  NewInventoryItem,
} from './model';

const itemSchema = z
  .object({
    id: z.number().int(),
    product_id: z.number().int(),
    product_name: z.string(),
    quantity: z.string(),
    unit_code: z.string(),
    minimum_quantity: z.string().nullable(),
    category_id: z.number().int().nullable(),
    category_name: z.string().nullable(),
    photo_url: z.string().nullable(),
    below_minimum: z.boolean(),
  })
  .transform((item): InventoryItem => ({
    id: item.id,
    productId: item.product_id,
    productName: item.product_name,
    quantity: item.quantity,
    unitCode: item.unit_code,
    minimumQuantity: item.minimum_quantity,
    categoryId: item.category_id,
    categoryName: item.category_name,
    photoUrl: item.photo_url,
    isBelowMinimum: item.below_minimum,
  }));

const categorySchema = z.object({ id: z.number().int(), name: z.string() });

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
    category_id: item.categoryId,
  };
  const response = await http.post('/inventory/', payload);
  return itemSchema.parse(response.data);
}

export async function updateInventoryItem(
  itemId: number,
  changes: Partial<InventoryItemChanges>,
): Promise<InventoryItem> {
  const payload = {
    product_name: changes.productName,
    quantity: changes.quantity,
    unit_code: changes.unitCode,
  };
  const response = await http.patch(`/inventory/${itemId}/`, payload);
  return itemSchema.parse(response.data);
}

export async function deleteInventoryItem(itemId: number): Promise<void> {
  await http.delete(`/inventory/${itemId}/`);
}

export async function fetchInventoryCategories(householdId: number): Promise<InventoryCategory[]> {
  const params = { household_id: householdId };
  const response = await http.get('/inventory/categories/', { params });
  return categorySchema.array().parse(response.data);
}

export async function createInventoryCategory(
  householdId: number,
  name: string,
): Promise<InventoryCategory> {
  const payload = { household_id: householdId, name };
  const response = await http.post('/inventory/categories/', payload);
  return categorySchema.parse(response.data);
}

export async function renameInventoryCategory(
  categoryId: number,
  name: string,
): Promise<InventoryCategory> {
  const response = await http.patch(`/inventory/categories/${categoryId}/`, { name });
  return categorySchema.parse(response.data);
}

export async function deleteInventoryCategory(categoryId: number): Promise<void> {
  await http.delete(`/inventory/categories/${categoryId}/`);
}

export async function setInventoryItemMinimum(
  itemId: number,
  minimumQuantity: string | null,
): Promise<InventoryItem> {
  const payload = { minimum_quantity: minimumQuantity };
  const response = await http.put(`/inventory/${itemId}/minimum/`, payload);
  return itemSchema.parse(response.data);
}

export async function setInventoryItemCategory(
  itemId: number,
  categoryId: number | null,
): Promise<InventoryItem> {
  const payload = { category_id: categoryId };
  const response = await http.put(`/inventory/${itemId}/category/`, payload);
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
