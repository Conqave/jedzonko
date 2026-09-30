import {
  isBaseUnit,
  matchesTagFilter,
  type MeasurementUnit,
  type ProductChanges,
  type TagFilter,
} from '@/features/catalog/model';
import { fromThousandths, toThousandths } from '@/shared/decimal';
import { sortByKeys, type SortKey } from '@/shared/listView';
import { matchesSearch } from '@/shared/textSearch';

export interface InventoryItem {
  id: number;
  productId: number;
  productName: string;
  quantity: string;
  unitCode: string;
  minimumQuantity: string | null;
  photoUrl: string | null;
  isBelowMinimum: boolean;
}

export interface NewInventoryItem {
  householdId: number;
  productId: number;
  quantity: string;
  unitCode: string;
  minimumQuantity: string | null;
}

export interface InventoryItemChanges {
  quantity: string;
  unitCode: string;
}

export interface InventoryItemEdit {
  changes: InventoryItemChanges;
  minimumQuantity: string | null;
}

export interface PantryItemEdit {
  product: ProductChanges;
  item: InventoryItemEdit;
}

export interface NewInventoryEntry {
  item: NewInventoryItem;
  photo: File | null;
}

export type QuantityDirection = -1 | 1;

const COUNT_STEP_THOUSANDTHS = 1000n;
const BASE_UNIT_STEP_THOUSANDTHS = 50000n;
const LARGE_UNIT_STEP_THOUSANDTHS = 100n;

function findStep(unit: MeasurementUnit): bigint {
  if (unit.dimension === 'count') {
    return COUNT_STEP_THOUSANDTHS;
  }
  return isBaseUnit(unit) ? BASE_UNIT_STEP_THOUSANDTHS : LARGE_UNIT_STEP_THOUSANDTHS;
}

export function stepQuantity(
  quantity: string,
  unit: MeasurementUnit,
  direction: QuantityDirection,
): string {
  const step = findStep(unit);
  const current = toThousandths(quantity);
  const next = current + BigInt(direction) * step;
  const clamped = next < 0n ? 0n : next;
  return fromThousandths(clamped);
}

export function isEmpty(quantity: string): boolean {
  return toThousandths(quantity) === 0n;
}

export const INVENTORY_SORTS = ['name', 'quantity', 'tag', 'belowMinimum'] as const;

export type InventorySort = (typeof INVENTORY_SORTS)[number];

export const INVENTORY_SORT_LABELS: Readonly<Record<InventorySort, string>> = {
  name: 'Nazwa',
  quantity: 'Ilość',
  tag: 'Tag',
  belowMinimum: 'Poniżej min.',
};

export interface InventoryView {
  search: string;
  tag: TagFilter;
  isBelowMinimumOnly: boolean;
  sort: InventorySort;
  isReversed: boolean;
}

interface InventoryEntry {
  item: InventoryItem;
  tagNames: string[];
}

function matchesInventoryView(entry: InventoryEntry, view: InventoryView): boolean {
  const matchesMinimum = !view.isBelowMinimumOnly || entry.item.isBelowMinimum;
  const matchesTag = matchesTagFilter(view.tag, entry.tagNames);
  const matchesText = matchesSearch(view.search, [entry.item.productName, ...entry.tagNames]);
  return matchesMinimum && matchesTag && matchesText;
}

function toBaseQuantityKeys(item: InventoryItem, units: readonly MeasurementUnit[]): SortKey[] {
  const unit = units.find((candidate) => candidate.code === item.unitCode);
  if (unit === undefined) {
    return [null, null];
  }
  const baseThousandths = toThousandths(item.quantity) * toThousandths(unit.factorToBase);
  return [unit.dimension, Number(baseThousandths)];
}

function toInventorySortKeys(
  entry: InventoryEntry,
  sort: InventorySort,
  units: readonly MeasurementUnit[],
): SortKey[] {
  const name = entry.item.productName;
  if (sort === 'name') {
    return [name];
  }
  if (sort === 'quantity') {
    return [...toBaseQuantityKeys(entry.item, units), name];
  }
  if (sort === 'tag') {
    const tagKey = entry.tagNames.length === 0 ? null : entry.tagNames.join(', ');
    return [tagKey, name];
  }
  return [entry.item.isBelowMinimum ? 0 : 1, name];
}

export function arrangeInventoryItems(
  items: InventoryItem[],
  view: InventoryView,
  findTags: (productId: number) => string[],
  units: readonly MeasurementUnit[],
): InventoryItem[] {
  const entries = items.map((item) => ({ item, tagNames: findTags(item.productId) }));
  const visible = entries.filter((entry) => matchesInventoryView(entry, view));
  const sorted = sortByKeys(
    visible,
    (entry) => toInventorySortKeys(entry, view.sort, units),
    view.isReversed,
  );
  return sorted.map((entry) => entry.item);
}
