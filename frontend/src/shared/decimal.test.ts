import { describe, expect, it } from 'vitest';
import {
  divideByThousand,
  fromThousandths,
  isNonNegativeDecimal,
  isPositiveDecimal,
  toDecimalText,
  toThousandths,
} from './decimal';

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

describe('decimal arithmetic', () => {
  it.each([
    ['1.500', 1500n],
    ['12', 12000n],
    ['0.05', 50n],
  ])('reads %s as %s thousandths', (value, expected) => {
    expect(toThousandths(value)).toBe(expected);
  });

  it('writes thousandths as a decimal', () => {
    expect(fromThousandths(1250n)).toBe('1.250');
  });

  it.each([
    ['5000.000', '5.000000'],
    ['1100', '1.100'],
    ['1234.567', '1.234567'],
    ['12', '0.012'],
  ])('divides %s by a thousand as %s', (value, expected) => {
    expect(divideByThousand(value)).toBe(expected);
  });
});
