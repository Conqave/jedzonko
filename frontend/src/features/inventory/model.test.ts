import { describe, expect, it } from 'vitest';
import type { MeasurementUnit } from '@/features/catalog/model';
import {
  arrangeInventoryItems,
  isEmpty,
  stepQuantity,
  type InventoryItem,
  type InventoryView,
} from './model';

const PIECE: MeasurementUnit = {
  code: 'szt',
  name: 'sztuka',
  dimension: 'count',
  factorToBase: '1.000',
};
const GRAM: MeasurementUnit = { code: 'g', name: 'gram', dimension: 'mass', factorToBase: '1.000' };
const KILOGRAM: MeasurementUnit = {
  code: 'kg',
  name: 'kilogram',
  dimension: 'mass',
  factorToBase: '1000.000',
};
const LITRE: MeasurementUnit = {
  code: 'l',
  name: 'litr',
  dimension: 'volume',
  factorToBase: '1000.000',
};

describe('stepQuantity', () => {
  it('steps counted units by one', () => {
    expect(stepQuantity('3.000', PIECE, 1)).toBe('4.000');
  });

  it('steps measured units by a tenth without float drift', () => {
    expect(stepQuantity('0.300', KILOGRAM, -1)).toBe('0.200');
    expect(stepQuantity('0.700', LITRE, 1)).toBe('0.800');
  });

  it('never goes below zero', () => {
    expect(stepQuantity('0.050', KILOGRAM, -1)).toBe('0.000');
  });
});

describe('isEmpty', () => {
  it('recognises a zero quantity', () => {
    expect(isEmpty('0.000')).toBe(true);
    expect(isEmpty('0.001')).toBe(false);
  });
});

describe('stepQuantity in base units', () => {
  it('moves grams by fifty', () => {
    expect(stepQuantity('500.000', GRAM, 1)).toBe('550.000');
  });
});

const FLOUR: InventoryItem = {
  id: 1,
  productId: 11,
  productName: 'Mąka tortowa',
  quantity: '1.500',
  unitCode: 'kg',
  minimumQuantity: '1.000',
  photoUrl: null,
  isBelowMinimum: false,
};
const SUGAR: InventoryItem = {
  ...FLOUR,
  id: 2,
  productId: 12,
  productName: 'Cukier',
  quantity: '800.000',
  unitCode: 'g',
  isBelowMinimum: true,
};
const EGGS: InventoryItem = {
  ...FLOUR,
  id: 3,
  productId: 13,
  productName: 'Jajka',
  quantity: '4.000',
  unitCode: 'szt',
  minimumQuantity: null,
};
const JUICE: InventoryItem = {
  ...FLOUR,
  id: 4,
  productId: 14,
  productName: 'Sok',
  quantity: '1.000',
  unitCode: 'l',
  isBelowMinimum: true,
};
const PANTRY = [FLOUR, SUGAR, EGGS, JUICE];
const UNITS = [PIECE, GRAM, KILOGRAM, LITRE];
const TAGS: ReadonlyMap<number, string[]> = new Map([
  [11, ['mąka']],
  [12, ['cukier']],
  [13, []],
  [14, []],
]);
const ALL: InventoryView = {
  search: '',
  tag: 'all',
  isBelowMinimumOnly: false,
  sort: 'name',
  isReversed: false,
};

function findTags(productId: number): string[] {
  return TAGS.get(productId) ?? [];
}

function arrangedNames(view: Partial<InventoryView>): string[] {
  const arranged = arrangeInventoryItems(PANTRY, { ...ALL, ...view }, findTags, UNITS);
  return arranged.map((item) => item.productName);
}

describe('arrangeInventoryItems', () => {
  it('sorts by product name', () => {
    expect(arrangedNames({})).toEqual(['Cukier', 'Jajka', 'Mąka tortowa', 'Sok']);
    expect(arrangedNames({ isReversed: true })).toEqual(['Sok', 'Mąka tortowa', 'Jajka', 'Cukier']);
  });

  it('sorts by quantity in base units, grouped by dimension', () => {
    expect(arrangedNames({ sort: 'quantity' })).toEqual(['Jajka', 'Cukier', 'Mąka tortowa', 'Sok']);
  });

  it('puts products without a known unit last when sorted by quantity', () => {
    const odd: InventoryItem = { ...EGGS, id: 5, productName: 'Szczypta', unitCode: 'szcz' };
    const arranged = arrangeInventoryItems(
      [odd, ...PANTRY],
      { ...ALL, sort: 'quantity' },
      findTags,
      UNITS,
    );

    expect(arranged.at(-1)).toEqual(odd);
  });

  it('sorts by tag with untagged products last', () => {
    expect(arrangedNames({ sort: 'tag' })).toEqual(['Cukier', 'Mąka tortowa', 'Jajka', 'Sok']);
  });

  it('puts products below their minimum first', () => {
    expect(arrangedNames({ sort: 'belowMinimum' })).toEqual([
      'Cukier',
      'Sok',
      'Jajka',
      'Mąka tortowa',
    ]);
  });

  it('filters by tag, minimum and search over product and tag names', () => {
    expect(arrangedNames({ tag: 'tagged' })).toEqual(['Cukier', 'Mąka tortowa']);
    expect(arrangedNames({ tag: 'untagged' })).toEqual(['Jajka', 'Sok']);
    expect(arrangedNames({ isBelowMinimumOnly: true })).toEqual(['Cukier', 'Sok']);
    expect(arrangedNames({ search: 'maka' })).toEqual(['Mąka tortowa']);
    expect(arrangedNames({ search: 'cukier', isBelowMinimumOnly: true })).toEqual(['Cukier']);
    expect(arrangedNames({ search: 'mleko' })).toEqual([]);
  });
});
