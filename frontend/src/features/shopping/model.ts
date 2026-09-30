import {
  matchesTagFilter,
  type Ingredient,
  type Product,
  type TagFilter,
} from '@/features/catalog/model';
import { sortByKeys, type SortKey } from '@/shared/listView';
import { matchesSearch } from '@/shared/textSearch';

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

export function reachesPantry(item: ShoppingItem): boolean {
  return item.subject.kind !== 'text';
}

export interface ShoppingPurchase {
  itemId: number;
  productId: number | null;
}

export interface PurchaseProductQuestion {
  item: ShoppingItem;
  products: Product[];
}

export function findPurchaseProductQuestions(
  items: ShoppingItem[],
  findTagProducts: (ingredientId: number) => Product[],
): PurchaseProductQuestion[] {
  const questions: PurchaseProductQuestion[] = [];
  for (const item of items) {
    if (item.subject.kind !== 'ingredient') {
      continue;
    }
    const products = findTagProducts(item.subject.ingredientId);
    if (products.length > 1) {
      questions.push({ item, products });
    }
  }
  return questions;
}

export function toPurchases(
  items: ShoppingItem[],
  chosenProducts: ReadonlyMap<number, number>,
): ShoppingPurchase[] {
  return items.map((item) => ({ itemId: item.id, productId: chosenProducts.get(item.id) ?? null }));
}

export function describeItemCount(count: number): string {
  const lastDigit = count % 10;
  const lastTwoDigits = count % 100;
  if (count === 1) {
    return '1 pozycję';
  }
  if (lastDigit >= 2 && lastDigit <= 4 && (lastTwoDigits < 12 || lastTwoDigits > 14)) {
    return `${String(count)} pozycje`;
  }
  return `${String(count)} pozycji`;
}

export const SHOPPING_STATUS_FILTERS = ['all', 'pending', 'purchased'] as const;

export type ShoppingStatusFilter = (typeof SHOPPING_STATUS_FILTERS)[number];

export const SHOPPING_STATUS_FILTER_LABELS: Readonly<Record<ShoppingStatusFilter, string>> = {
  all: 'Wszystkie',
  pending: 'Do kupienia',
  purchased: 'Kupione',
};

export const SHOPPING_SORTS = ['added', 'name', 'tag'] as const;

export type ShoppingSort = (typeof SHOPPING_SORTS)[number];

export const SHOPPING_SORT_LABELS: Readonly<Record<ShoppingSort, string>> = {
  added: 'Dodano',
  name: 'Nazwa',
  tag: 'Tag',
};

export interface ShoppingItemView {
  search: string;
  status: ShoppingStatusFilter;
  tag: TagFilter;
  sort: ShoppingSort;
  isReversed: boolean;
}

export function findShoppingItemTags(
  item: ShoppingItem,
  findProductTags: (productId: number) => string[],
): string[] {
  if (item.subject.kind === 'product') {
    return findProductTags(item.subject.productId);
  }
  if (item.subject.kind === 'ingredient') {
    return [item.name];
  }
  return [];
}

interface ShoppingItemEntry {
  item: ShoppingItem;
  tagNames: string[];
  position: number;
}

function matchesShoppingItemView(entry: ShoppingItemEntry, view: ShoppingItemView): boolean {
  const matchesStatus = view.status === 'all' || entry.item.status === view.status;
  const matchesTag = matchesTagFilter(view.tag, entry.tagNames);
  const matchesText = matchesSearch(view.search, [entry.item.name, ...entry.tagNames]);
  return matchesStatus && matchesTag && matchesText;
}

function toShoppingSortKeys(entry: ShoppingItemEntry, sort: ShoppingSort): SortKey[] {
  if (sort === 'added') {
    return [-entry.position];
  }
  if (sort === 'name') {
    return [entry.item.name];
  }
  const tagKey = entry.tagNames.length === 0 ? null : entry.tagNames.join(', ');
  return [tagKey, entry.item.name];
}

export function arrangeShoppingItems(
  itemsInAddedOrder: ShoppingItem[],
  view: ShoppingItemView,
  findProductTags: (productId: number) => string[],
): ShoppingItem[] {
  const entries = itemsInAddedOrder.map((item, position) => ({
    item,
    tagNames: findShoppingItemTags(item, findProductTags),
    position,
  }));
  const visible = entries.filter((entry) => matchesShoppingItemView(entry, view));
  const sorted = sortByKeys(
    visible,
    (entry) => toShoppingSortKeys(entry, view.sort),
    view.isReversed,
  );
  return sorted.map((entry) => entry.item);
}

export function findVisibleSelection(
  visibleItems: ShoppingItem[],
  selectedIds: readonly number[],
): ShoppingItem[] {
  const selected = new Set(selectedIds);
  return visibleItems.filter((item) => selected.has(item.id));
}
