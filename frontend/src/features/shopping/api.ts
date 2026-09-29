import { z } from 'zod';
import { http } from '@/shared/http';
import {
  SHOPPING_ITEM_STATUSES,
  type NewShoppingItem,
  type RecipeShoppingSource,
  type ShoppingItem,
  type ShoppingList,
  type ShoppingSubject,
} from './model';

const listSchema = z
  .object({
    id: z.number().int(),
    household_id: z.number().int(),
    name: z.string(),
    is_primary: z.boolean(),
    item_count: z.number().int(),
  })
  .transform((value): ShoppingList => ({
    id: value.id,
    householdId: value.household_id,
    name: value.name,
    isPrimary: value.is_primary,
    itemCount: value.item_count,
  }));

const subjectFields = z.union([
  z.object({ product_id: z.number().int(), ingredient_id: z.null(), free_text: z.null() }),
  z.object({ product_id: z.null(), ingredient_id: z.number().int(), free_text: z.null() }),
  z.object({ product_id: z.null(), ingredient_id: z.null(), free_text: z.string() }),
]);

function toSubject(fields: z.infer<typeof subjectFields>): ShoppingSubject {
  if (fields.product_id !== null) {
    return { kind: 'product', productId: fields.product_id };
  }
  if (fields.ingredient_id !== null) {
    return { kind: 'ingredient', ingredientId: fields.ingredient_id };
  }
  return { kind: 'text', text: fields.free_text };
}

const itemSchema = z
  .object({
    id: z.number().int(),
    list_id: z.number().int(),
    name: z.string(),
    quantity: z.string(),
    unit_code: z.string().nullable(),
    status: z.enum(SHOPPING_ITEM_STATUSES),
    purchased_at: z.iso.datetime({ offset: true }).nullable(),
  })
  .and(subjectFields)
  .transform((value): ShoppingItem => ({
    id: value.id,
    listId: value.list_id,
    subject: toSubject(value),
    name: value.name,
    quantity: value.quantity,
    unitCode: value.unit_code,
    status: value.status,
    purchasedAt: value.purchased_at === null ? null : new Date(value.purchased_at),
  }));

function toSubjectPayload(subject: ShoppingSubject) {
  return {
    product_id: subject.kind === 'product' ? subject.productId : null,
    ingredient_id: subject.kind === 'ingredient' ? subject.ingredientId : null,
    free_text: subject.kind === 'text' ? subject.text : null,
  };
}

function toRecipeRequest(listId: number, source: RecipeShoppingSource) {
  if (source.kind === 'recipe') {
    const body = { recipe_id: source.recipeId, servings: source.servings };
    return { url: `/shopping/lists/${listId}/recipe-items/`, body };
  }
  const body = { reference: source.reference };
  return { url: `/shopping/lists/${listId}/external-recipe-items/`, body };
}

export async function fetchShoppingLists(householdId: number): Promise<ShoppingList[]> {
  const response = await http.get('/shopping/lists/', { params: { household_id: householdId } });
  return listSchema.array().parse(response.data);
}

export async function createShoppingList(householdId: number, name: string): Promise<ShoppingList> {
  const response = await http.post('/shopping/lists/', { household_id: householdId, name });
  return listSchema.parse(response.data);
}

export async function renameShoppingList(listId: number, name: string): Promise<ShoppingList> {
  const response = await http.patch(`/shopping/lists/${listId}/`, { name });
  return listSchema.parse(response.data);
}

export async function deleteShoppingList(listId: number): Promise<void> {
  await http.delete(`/shopping/lists/${listId}/`);
}

export async function fetchShoppingItems(listId: number): Promise<ShoppingItem[]> {
  const response = await http.get(`/shopping/lists/${listId}/items/`);
  return itemSchema.array().parse(response.data);
}

export async function addShoppingItem(
  listId: number,
  item: NewShoppingItem,
): Promise<ShoppingItem> {
  const subject = toSubjectPayload(item.subject);
  const payload = { ...subject, quantity: item.quantity, unit_code: item.unitCode };
  const response = await http.post(`/shopping/lists/${listId}/items/`, payload);
  return itemSchema.parse(response.data);
}

export async function addRecipeItems(
  listId: number,
  source: RecipeShoppingSource,
): Promise<ShoppingItem[]> {
  const request = toRecipeRequest(listId, source);
  const response = await http.post(request.url, request.body);
  return itemSchema.array().parse(response.data);
}

export async function synchronizeMinimumStock(householdId: number): Promise<ShoppingItem[]> {
  const response = await http.post(`/shopping/households/${householdId}/minimum-stock/`);
  return itemSchema.array().parse(response.data);
}

export async function splitByPromotions(
  listId: number,
  shopSlugs: string[],
): Promise<ShoppingList[]> {
  const payload = { shops: shopSlugs };
  const response = await http.post(`/shopping/lists/${listId}/promotion-split/`, payload);
  return listSchema.array().parse(response.data);
}

export async function buyShoppingItems(listId: number, itemIds: number[]): Promise<void> {
  await http.post(`/shopping/lists/${listId}/purchase/`, { item_ids: itemIds });
}

export async function chooseShoppingItemProduct(
  itemId: number,
  productId: number,
): Promise<ShoppingItem> {
  const payload = { product_id: productId };
  const response = await http.put(`/shopping/items/${itemId}/product/`, payload);
  return itemSchema.parse(response.data);
}

export async function restoreShoppingItem(itemId: number): Promise<ShoppingItem> {
  const response = await http.post(`/shopping/items/${itemId}/restore/`);
  return itemSchema.parse(response.data);
}

export async function deleteShoppingItem(itemId: number): Promise<void> {
  await http.delete(`/shopping/items/${itemId}/`);
}
