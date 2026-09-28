import { http as api } from '@/shared/http';
import type { NewShoppingItem, ShoppingItem, ShoppingList } from './models';

export async function fetchShoppingLists(householdId: number): Promise<ShoppingList[]> {
  const response = await api.get<ShoppingList[]>('/shopping/lists/', {
    params: { household_id: householdId },
  });
  return response.data;
}

export async function createShoppingList(householdId: number, name: string): Promise<ShoppingList> {
  const response = await api.post<ShoppingList>('/shopping/lists/', {
    household_id: householdId,
    name,
  });
  return response.data;
}

export async function fetchShoppingItems(listId: number): Promise<ShoppingItem[]> {
  const response = await api.get<ShoppingItem[]>(`/shopping/lists/${listId}/items/`);
  return response.data;
}

export async function addShoppingItem(
  listId: number,
  item: NewShoppingItem,
): Promise<ShoppingItem> {
  const response = await api.post<ShoppingItem>(`/shopping/lists/${listId}/items/`, item);
  return response.data;
}

export async function addRecipeItems(
  listId: number,
  recipeId: number,
  servings: number,
): Promise<ShoppingItem[]> {
  const response = await api.post<ShoppingItem[]>(`/shopping/lists/${listId}/items/from-recipe/`, {
    recipe_id: recipeId,
    servings,
  });
  return response.data;
}

export async function synchronizeMinimumStock(listId: number): Promise<ShoppingItem[]> {
  const response = await api.post<ShoppingItem[]>(
    `/shopping/lists/${listId}/synchronize-minimum-stock/`,
  );
  return response.data;
}

export async function buyShoppingItem(itemId: number): Promise<void> {
  await api.post(`/shopping/items/${itemId}/buy/`);
}

export async function restorePurchasedShoppingItem(itemId: number): Promise<void> {
  await api.post(`/shopping/purchased-items/${itemId}/restore/`);
}

export async function deleteShoppingItem(itemId: number): Promise<void> {
  await api.delete(`/shopping/items/${itemId}/`);
}

export async function deleteShoppingList(listId: number): Promise<void> {
  await api.delete(`/shopping/lists/${listId}/`);
}

export async function renameShoppingList(listId: number, name: string): Promise<ShoppingList> {
  const response = await api.patch<ShoppingList>(`/shopping/lists/${listId}/`, { name });
  return response.data;
}
