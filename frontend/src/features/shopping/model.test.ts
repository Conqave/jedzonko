import { describe, expect, it } from 'vitest';
import { hasAmount, orderPrimaryFirst, reachesPantry, type ShoppingItem } from './model';

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
  it('stocks a product and an ingredient with exactly one product', () => {
    const product: ShoppingItem = { ...ITEM, subject: { kind: 'product', productId: 3 } };

    expect(reachesPantry(product, () => 0)).toBe(true);
    expect(reachesPantry(ITEM, () => 1)).toBe(true);
  });

  it('does not stock text lines or ingredients without a single product', () => {
    expect(reachesPantry(TEXT_ITEM, () => 1)).toBe(false);
    expect(reachesPantry(ITEM, () => 0)).toBe(false);
    expect(reachesPantry(ITEM, () => 2)).toBe(false);
  });
});
