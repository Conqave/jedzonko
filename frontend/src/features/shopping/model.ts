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

export type ShoppingItemStatus = 'pending' | 'purchased';

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
