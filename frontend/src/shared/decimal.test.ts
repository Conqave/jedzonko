import { describe, expect, it } from 'vitest';
import { isNonNegativeDecimal, isPositiveDecimal, toDecimalText } from './decimal';

describe('decimal input', () => {
  it.each(['1', '0.5', '2,25', '12.125'])('accepts %s', (value) => {
    expect(isPositiveDecimal(value)).toBe(true);
  });

  it.each(['', '0', '0,000', '-1', '1.2345', 'abc', '1e3'])('rejects %s', (value) => {
    expect(isPositiveDecimal(value)).toBe(false);
  });

  it.each(['0', ' 0 ', '1,5'])('accepts %s as a non-negative quantity', (value) => {
    expect(isNonNegativeDecimal(value)).toBe(true);
  });

  it.each(['', '-1', 'abc'])('rejects %s as a non-negative quantity', (value) => {
    expect(isNonNegativeDecimal(value)).toBe(false);
  });

  it('writes a decimal comma as a point', () => {
    expect(toDecimalText(' 2,5 ')).toBe('2.5');
  });
});
