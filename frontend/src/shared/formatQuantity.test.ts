import { describe, expect, it } from 'vitest';
import { formatQuantity } from './formatQuantity';

const CASES: ReadonlyArray<readonly [string, string]> = [
  ['2.000', '2'],
  ['1.500', '1,5'],
  ['0.850', '0,85'],
  ['0.125', '0,125'],
  ['12', '12'],
  ['0.000', '0'],
  ['0.10000000000000000555', '0,10000000000000000555'],
  ['9007199254740993.500', '9007199254740993,5'],
  ['-1.500', '-1,5'],
  ['', ''],
];

describe('formatQuantity', () => {
  it.each(CASES)('shows %s as %s', (input, expected) => {
    expect(formatQuantity(input)).toBe(expected);
  });
});
