import type { Ingredient } from '@/features/catalog/model';

export interface ShoppingList {
  id: number;
  householdId: number;
  name: string;
  isPrimary: boolean;
  itemCount: number;
}

export type ShoppingSubject =
  | { kind: 'product'; productId: number }
  | { kind: 'ingredient'; ingredientId: number }
  | { kind: 'text'; text: string };

export const SHOPPING_ITEM_STATUSES = ['pending', 'purchased'] as const;

export type ShoppingItemStatus = (typeof SHOPPING_ITEM_STATUSES)[number];

export interface ShoppingItem {
  id: number;
  listId: number;
  subject: ShoppingSubject;
  name: string;
  quantity: string;
  unitCode: string | null;
  status: ShoppingItemStatus;
  purchasedAt: Date | null;
}

export interface NewShoppingItem {
  subject: ShoppingSubject;
  quantity: string;
  unitCode: string | null;
}

export const COUNT_UNIT_CODE = 'szt';

export interface ShoppingItemTagging {
  ingredientId: number;
  quantity: string;
  unitCode: string;
}

export interface ShoppingItemTagRequest {
  tagging: ShoppingItemTagging;
  productId: number | null;
}

export interface ShoppingItemInterpretation {
  ingredient: Ingredient | null;
  quantity: string | null;
  unitCode: string | null;
}

export type RecipeShoppingSource =
  { kind: 'recipe'; recipeId: number; servings: number } | { kind: 'external'; reference: string };

export interface ShopOption {
  slug: string;
  name: string;
}

export function orderPrimaryFirst(lists: ShoppingList[]): ShoppingList[] {
  const primary = lists.filter((list) => list.isPrimary);
  const others = lists.filter((list) => !list.isPrimary);
  return [...primary, ...others];
}

export function hasAmount(item: ShoppingItem): boolean {
  return item.subject.kind !== 'text';
}

export function reachesPantry(
  item: ShoppingItem,
  countIngredientProducts: (ingredientId: number) => number,
): boolean {
  if (item.subject.kind === 'product') {
    return true;
  }
  if (item.subject.kind === 'ingredient') {
    return countIngredientProducts(item.subject.ingredientId) === 1;
  }
  return false;
}
