const POSITIVE_DECIMAL = /^\d+([.,]\d{1,3})?$/;

export function isPositiveDecimal(value: string): boolean {
  const trimmed = value.trim();
  return POSITIVE_DECIMAL.test(trimmed) && Number(toDecimalText(trimmed)) > 0;
}

export function toDecimalText(value: string): string {
  return value.trim().replace(',', '.');
}
