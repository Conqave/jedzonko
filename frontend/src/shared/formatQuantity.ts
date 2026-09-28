const DECIMAL_PATTERN = /^-?\d+(\.\d+)?$/;

export function formatQuantity(value: string): string {
  const trimmed = value.trim();
  if (!DECIMAL_PATTERN.test(trimmed)) {
    return trimmed;
  }
  if (!trimmed.includes('.')) {
    return trimmed;
  }
  const withoutTrailingZeroes = trimmed.replace(/0+$/, '').replace(/\.$/, '');
  return withoutTrailingZeroes === '' || withoutTrailingZeroes === '-'
    ? '0'
    : withoutTrailingZeroes;
}
