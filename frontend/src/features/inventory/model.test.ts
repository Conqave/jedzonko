import { describe, expect, it } from 'vitest';
import type { MeasurementUnit } from '@/features/catalog/model';
import { isEmpty, stepQuantity } from './model';

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
