import { describe, expect, it } from 'vitest';
import type { Product } from '@/features/catalog/model';
import {
  findPurchaseProductQuestions,
  hasAmount,
  orderPrimaryFirst,
  reachesPantry,
  toPurchases,
  type ShoppingItem,
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
