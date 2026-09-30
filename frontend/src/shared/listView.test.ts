import { describe, expect, it } from 'vitest';
import { sortByKeys, type SortKey } from './listView';

interface Row {
  name: string;
  kcal: number | null;
}

const ROWS: Row[] = [
  { name: 'żurek', kcal: 300 },
  { name: 'Zupa', kcal: null },
  { name: 'łosoś', kcal: 450 },
  { name: 'lody', kcal: 200 },
  { name: 'ćwikła', kcal: null },
  { name: 'Ciasto', kcal: 450 },
];

function byName(row: Row): SortKey[] {
  return [row.name];
}

function byKcal(row: Row): SortKey[] {
  return [row.kcal, row.name];
}

function names(rows: Row[]): string[] {
  return rows.map((row) => row.name);
}

describe('list sorting', () => {
  it('orders words by Polish collation, ignoring case', () => {
    const sorted = sortByKeys(ROWS, byName, false);

    expect(names(sorted)).toEqual(['Ciasto', 'ćwikła', 'lody', 'łosoś', 'Zupa', 'żurek']);
  });

  it('reverses the order on request', () => {
    const sorted = sortByKeys(ROWS, byName, true);

    expect(names(sorted)).toEqual(['żurek', 'Zupa', 'łosoś', 'lody', 'ćwikła', 'Ciasto']);
  });

  it('breaks ties with the next key and keeps missing values last both ways', () => {
    const ascending = sortByKeys(ROWS, byKcal, false);
    const descending = sortByKeys(ROWS, byKcal, true);

    expect(names(ascending)).toEqual(['lody', 'żurek', 'Ciasto', 'łosoś', 'ćwikła', 'Zupa']);
    expect(names(descending)).toEqual(['łosoś', 'Ciasto', 'żurek', 'lody', 'Zupa', 'ćwikła']);
  });

  it('compares numbers in text naturally', () => {
    const sorted = sortByKeys(['Lista 10', 'Lista 9'], (text) => [text], false);

    expect(sorted).toEqual(['Lista 9', 'Lista 10']);
  });

  it('leaves the input untouched', () => {
    const input = [...ROWS];

    sortByKeys(input, byName, false);

    expect(input).toEqual(ROWS);
  });

  it('rejects keys of different types at one position', () => {
    const mixed: SortKey[][] = [['a'], [1]];

    expect(() => sortByKeys(mixed, (keys) => keys, false)).toThrow();
  });
});
