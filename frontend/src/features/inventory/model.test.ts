import { describe, expect, it } from 'vitest';
import { isEmpty, stepQuantity } from './model';

describe('stepQuantity', () => {
  it('steps counted units by one', () => {
    expect(stepQuantity('3.000', 'count', 1)).toBe('4.000');
  });

  it('steps measured units by a tenth without float drift', () => {
    expect(stepQuantity('0.300', 'mass', -1)).toBe('0.200');
    expect(stepQuantity('0.700', 'volume', 1)).toBe('0.800');
  });

  it('never goes below zero', () => {
    expect(stepQuantity('0.050', 'mass', -1)).toBe('0.000');
  });
});

describe('isEmpty', () => {
  it('recognises a zero quantity', () => {
    expect(isEmpty('0.000')).toBe(true);
    expect(isEmpty('0.001')).toBe(false);
  });
});
