import { describe, expect, it } from 'vitest';
import { orderPrimaryFirst } from './model';

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
