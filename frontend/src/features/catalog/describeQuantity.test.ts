import { describe, expect, it } from 'vitest';
import { describeQuantity } from './describeQuantity';

describe('describeQuantity', () => {
  it.each([
    ['1.000', 'l', '1 litr'],
    ['2.000', 'l', '2 litry'],
    ['5', 'l', '5 litrów'],
    ['22', 'szt', '22 sztuki'],
    ['12', 'szt', '12 sztuk'],
    ['1.500', 'kg', '1.5 kilograma'],
    ['250', 'g', '250 gramów'],
    ['3', 'box', '3 pudełko'],
  ])('describes %s %s as %s', (quantity, unitCode, expected) => {
    expect(describeQuantity(quantity, unitCode, 'pudełko')).toBe(expected);
  });
});
