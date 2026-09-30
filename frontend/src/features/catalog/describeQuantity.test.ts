import { describe, expect, it } from 'vitest';
import { describeQuantity } from './describeQuantity';
import type { MeasurementUnit } from './model';

const UNITS: readonly MeasurementUnit[] = [
  { code: 'g', name: 'gram', dimension: 'mass', factorToBase: '1.000' },
  { code: 'kg', name: 'kilogram', dimension: 'mass', factorToBase: '1000.000' },
  { code: 'ml', name: 'mililitr', dimension: 'volume', factorToBase: '1.000' },
  { code: 'l', name: 'litr', dimension: 'volume', factorToBase: '1000.000' },
  { code: 'szt', name: 'sztuka', dimension: 'count', factorToBase: '1.000' },
  { code: 'box', name: 'pudełko', dimension: 'count', factorToBase: '1.000' },
];

describe('describeQuantity', () => {
  it.each([
    ['1.000', 'l', '1 litr'],
    ['2.000', 'l', '2 litry'],
    ['5', 'l', '5 litrów'],
    ['22', 'szt', '22 sztuki'],
    ['12', 'szt', '12 sztuk'],
    ['1.500', 'kg', '1,5 kilograma'],
    ['250', 'g', '250 gramów'],
    ['999.500', 'g', '999,5 grama'],
    ['3', 'box', '3 pudełko'],
    ['3', 'unknown', '3 unknown'],
  ])('describes %s %s as %s', (quantity, unitCode, expected) => {
    expect(describeQuantity(quantity, unitCode, UNITS)).toBe(expected);
  });

  it.each([
    ['1000.000', 'g', '1 kilogram'],
    ['5000.000', 'g', '5 kilogramów'],
    ['1100.000', 'g', '1,1 kilograma'],
    ['2000', 'g', '2 kilogramy'],
    ['1234.567', 'g', '1,234567 kilograma'],
    ['1500.000', 'ml', '1,5 litra'],
    ['22000', 'ml', '22 litry'],
    ['1500', 'szt', '1500 sztuk'],
    ['2500.000', 'kg', '2500 kilogramów'],
  ])('shows %s %s in a larger unit as %s', (quantity, unitCode, expected) => {
    expect(describeQuantity(quantity, unitCode, UNITS)).toBe(expected);
  });
});
