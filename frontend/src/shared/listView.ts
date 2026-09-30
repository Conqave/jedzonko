export type SortKey = string | number | null;

export const NO_MATCHES_LABEL = 'Nic nie pasuje do wyszukiwania i filtrów.';

const POLISH_COLLATOR = new Intl.Collator('pl', { sensitivity: 'base', numeric: true });

function compareValues(left: string | number, right: string | number): number {
  if (typeof left === 'string' && typeof right === 'string') {
    return POLISH_COLLATOR.compare(left, right);
  }
  if (typeof left === 'number' && typeof right === 'number') {
    return left - right;
  }
  throw new Error('Sort keys at one position must share a type.');
}

function compareKeys(left: SortKey, right: SortKey, isReversed: boolean): number {
  if (left === null || right === null) {
    if (left === right) {
      return 0;
    }
    return left === null ? 1 : -1;
  }
  const order = compareValues(left, right);
  return isReversed ? -order : order;
}

function compareKeyLists(
  left: readonly SortKey[],
  right: readonly SortKey[],
  isReversed: boolean,
): number {
  for (const [index, leftKey] of left.entries()) {
    const rightKey = right[index];
    if (rightKey === undefined) {
      throw new Error('Sort key lists must have the same length.');
    }
    const order = compareKeys(leftKey, rightKey, isReversed);
    if (order !== 0) {
      return order;
    }
  }
  return 0;
}

export function sortByKeys<Item>(
  items: readonly Item[],
  toKeys: (item: Item) => readonly SortKey[],
  isReversed: boolean,
): Item[] {
  const keyed = items.map((item) => ({ item, keys: toKeys(item) }));
  const sorted = keyed.toSorted((left, right) =>
    compareKeyLists(left.keys, right.keys, isReversed),
  );
  return sorted.map((entry) => entry.item);
}
