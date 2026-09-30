import { describe, expect, it } from 'vitest';
import type { Product } from '@/features/catalog/model';
import {
  arrangeShoppingItems,
  describeItemCount,
  findShoppingItemTags,
  findVisibleSelection,
  findPurchaseProductQuestions,
  hasAmount,
  orderPrimaryFirst,
  reachesPantry,
  toPurchases,
  type ShoppingItem,
  type ShoppingItemView,
} from './model';

describe('orderPrimaryFirst', () => {
  it('puts the primary list first and keeps the rest in order', () => {
    const lists = [
      { id: 1, householdId: 1, name: 'Biedronka', isPrimary: false, itemCount: 2 },
      { id: 2, householdId: 1, name: 'Lista zakupów', isPrimary: true, itemCount: 5 },
      { id: 3, householdId: 1, name: 'Lidl', isPrimary: false, itemCount: 1 },
    ];

    const ordered = orderPrimaryFirst(lists);

    expect(ordered.map((list) => list.id)).toEqual([2, 1, 3]);
  });
});

const ITEM: ShoppingItem = {
  id: 1,
  listId: 1,
  subject: { kind: 'ingredient', ingredientId: 9 },
  name: 'jajka',
  quantity: '6.000',
  unitCode: 'szt',
  status: 'pending',
  purchasedAt: null,
  calories: { kind: 'counted', kcal: '429.0', kcalPer100g: '143.0', isEstimate: true },
};

const TEXT_ITEM: ShoppingItem = {
  ...ITEM,
  subject: { kind: 'text', text: '2 litry mleka' },
  unitCode: null,
};

describe('hasAmount', () => {
  it('hides the amount of an untagged text line', () => {
    expect(hasAmount(TEXT_ITEM)).toBe(false);
    expect(hasAmount(ITEM)).toBe(true);
  });
});

describe('reachesPantry', () => {
  it('stocks products and tagged items', () => {
    const product: ShoppingItem = { ...ITEM, subject: { kind: 'product', productId: 3 } };

    expect(reachesPantry(product)).toBe(true);
    expect(reachesPantry(ITEM)).toBe(true);
  });

  it('does not stock untagged text lines', () => {
    expect(reachesPantry(TEXT_ITEM)).toBe(false);
  });
});

function makeProduct(id: number, name: string): Product {
  return { id, householdId: 1, name, defaultUnitCode: 'szt', isFood: true, package: null };
}

describe('findPurchaseProductQuestions', () => {
  it('asks only about tagged items carried by several products', () => {
    const cage = makeProduct(3, 'Jajka klatkowe');
    const free = makeProduct(4, 'Jajka z wolnego wybiegu');
    const milk: ShoppingItem = { ...ITEM, id: 2, subject: { kind: 'ingredient', ingredientId: 7 } };
    const product: ShoppingItem = { ...ITEM, id: 3, subject: { kind: 'product', productId: 3 } };
    const products = new Map([
      [9, [cage, free]],
      [7, [makeProduct(5, 'Mleko')]],
    ]);

    const questions = findPurchaseProductQuestions(
      [ITEM, milk, product, TEXT_ITEM],
      (ingredientId) => products.get(ingredientId) ?? [],
    );

    expect(questions).toEqual([{ item: ITEM, products: [cage, free] }]);
  });
});

describe('toPurchases', () => {
  it('adds the chosen product only to items it was chosen for', () => {
    const bread: ShoppingItem = { ...TEXT_ITEM, id: 2 };
    const purchases = toPurchases([ITEM, bread], new Map([[ITEM.id, 4]]));

    expect(purchases).toEqual([
      { itemId: ITEM.id, productId: 4 },
      { itemId: bread.id, productId: null },
    ]);
  });
});

describe('describeItemCount', () => {
  it('counts items in the accusative Polish plural', () => {
    const counts = [1, 2, 4, 5, 12, 14, 21, 22, 25, 112, 122];

    expect(counts.map(describeItemCount)).toEqual([
      '1 pozycję',
      '2 pozycje',
      '4 pozycje',
      '5 pozycji',
      '12 pozycji',
      '14 pozycji',
      '21 pozycji',
      '22 pozycje',
      '25 pozycji',
      '112 pozycji',
      '122 pozycje',
    ]);
  });
});

const PRODUCT_TAGS: ReadonlyMap<number, string[]> = new Map([
  [7, ['Nabiał', 'Ser']],
  [8, []],
]);

function findProductTags(productId: number): string[] {
  return PRODUCT_TAGS.get(productId) ?? [];
}

const EGGS: ShoppingItem = ITEM;
const CHEESE: ShoppingItem = {
  ...ITEM,
  id: 2,
  subject: { kind: 'product', productId: 7 },
  name: 'Gouda plastry',
};
const MILK_NOTE: ShoppingItem = { ...TEXT_ITEM, id: 3, name: 'Mleko łaciate' };
const BREAD: ShoppingItem = {
  ...ITEM,
  id: 4,
  subject: { kind: 'product', productId: 8 },
  name: 'Chleb żytni',
  status: 'purchased',
  purchasedAt: new Date('2026-09-01T10:00:00Z'),
};
const ADDED_ORDER = [EGGS, CHEESE, MILK_NOTE, BREAD];
const EVERYTHING: ShoppingItemView = {
  search: '',
  status: 'all',
  tag: 'all',
  sort: 'added',
  isReversed: false,
};

function arrangedIds(view: Partial<ShoppingItemView>): number[] {
  const arranged = arrangeShoppingItems(ADDED_ORDER, { ...EVERYTHING, ...view }, findProductTags);
  return arranged.map((item) => item.id);
}

describe('findShoppingItemTags', () => {
  it('names the tags of a product, the ingredient itself, and none for a text line', () => {
    expect(findShoppingItemTags(CHEESE, findProductTags)).toEqual(['Nabiał', 'Ser']);
    expect(findShoppingItemTags(EGGS, findProductTags)).toEqual(['jajka']);
    expect(findShoppingItemTags(MILK_NOTE, findProductTags)).toEqual([]);
  });
});

describe('arrangeShoppingItems', () => {
  it('shows the newest item first when sorted by date added', () => {
    expect(arrangedIds({})).toEqual([4, 3, 2, 1]);
    expect(arrangedIds({ isReversed: true })).toEqual([1, 2, 3, 4]);
  });

  it('sorts by name in Polish order', () => {
    expect(arrangedIds({ sort: 'name' })).toEqual([4, 2, 1, 3]);
  });

  it('sorts by tag with untagged items last in either direction', () => {
    expect(arrangedIds({ sort: 'tag' })).toEqual([1, 2, 4, 3]);
    expect(arrangedIds({ sort: 'tag', isReversed: true })).toEqual([2, 1, 3, 4]);
  });

  it('filters by status', () => {
    expect(arrangedIds({ status: 'pending' })).toEqual([3, 2, 1]);
    expect(arrangedIds({ status: 'purchased' })).toEqual([4]);
  });

  it('filters by having a tag', () => {
    expect(arrangedIds({ tag: 'tagged' })).toEqual([2, 1]);
    expect(arrangedIds({ tag: 'untagged' })).toEqual([4, 3]);
  });

  it('searches item names and tag names without diacritics', () => {
    expect(arrangedIds({ search: 'nabial' })).toEqual([2]);
    expect(arrangedIds({ search: 'LACIATE' })).toEqual([3]);
    expect(arrangedIds({ search: 'zytni' })).toEqual([4]);
    expect(arrangedIds({ search: 'ser gouda' })).toEqual([2]);
    expect(arrangedIds({ search: 'ser', status: 'purchased' })).toEqual([]);
  });
});

describe('findVisibleSelection', () => {
  it('acts only on ticked items that the filters still show', () => {
    const visible = arrangeShoppingItems(
      ADDED_ORDER,
      { ...EVERYTHING, status: 'pending', search: 'jajka' },
      findProductTags,
    );

    const selected = findVisibleSelection(visible, [1, 2, 3]);

    expect(selected.map((item) => item.id)).toEqual([1]);
  });

  it('ignores ticks of items that are gone', () => {
    expect(findVisibleSelection([EGGS], [99])).toEqual([]);
  });
});
