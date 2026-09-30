const POSITIVE_DECIMAL = /^\d+([.,]\d{1,3})?$/;

export function isPositiveDecimal(value: string): boolean {
  const trimmed = value.trim();
  return POSITIVE_DECIMAL.test(trimmed) && Number(toDecimalText(trimmed)) > 0;
}

export function isNonNegativeDecimal(value: string): boolean {
  return value.trim() === '0' || isPositiveDecimal(value);
}

export function toDecimalText(value: string): string {
  return value.trim().replace(',', '.');
}

const THOUSANDTHS_PER_UNIT = 1000n;
const THOUSANDTHS_DIGITS = 3;

export function toThousandths(value: string): bigint {
  const [whole = '0', fraction = ''] = value.split('.');
  const paddedFraction = fraction.padEnd(THOUSANDTHS_DIGITS, '0').slice(0, THOUSANDTHS_DIGITS);
  return BigInt(whole) * THOUSANDTHS_PER_UNIT + BigInt(paddedFraction);
}

export function fromThousandths(thousandths: bigint): string {
  const whole = thousandths / THOUSANDTHS_PER_UNIT;
  const fraction = thousandths % THOUSANDTHS_PER_UNIT;
  const paddedFraction = fraction.toString().padStart(THOUSANDTHS_DIGITS, '0');
  return `${whole.toString()}.${paddedFraction}`;
}

export function divideByThousand(value: string): string {
  const [whole = '0', fraction = ''] = value.split('.');
  const paddedWhole = whole.padStart(THOUSANDTHS_DIGITS + 1, '0');
  const splitIndex = paddedWhole.length - THOUSANDTHS_DIGITS;
  const shiftedWhole = paddedWhole.slice(0, splitIndex);
  const shiftedFraction = `${paddedWhole.slice(splitIndex)}${fraction}`;
  return `${shiftedWhole}.${shiftedFraction}`;
}
