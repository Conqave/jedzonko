import type { MeasurementDimension } from '@/features/catalog/model';

export interface InventoryItem {
  id: number;
  productId: number;
  productName: string;
  quantity: string;
  unitCode: string;
  minimumQuantity: string | null;
  categoryId: number | null;
  categoryName: string | null;
  photoUrl: string | null;
  isBelowMinimum: boolean;
}

export interface InventoryCategory {
  id: number;
  name: string;
}

export interface NewInventoryItem {
  householdId: number;
  productId: number;
  quantity: string;
  unitCode: string;
  minimumQuantity: string | null;
  categoryId: number | null;
}

export interface InventoryItemChanges {
  productName: string;
  quantity: string;
  unitCode: string;
}

export interface InventoryItemEdit {
  changes: InventoryItemChanges;
  minimumQuantity: string | null;
}

export interface NewInventoryEntry {
  item: NewInventoryItem;
  photo: File | null;
}

export type QuantityDirection = -1 | 1;

const THOUSANDTHS_PER_UNIT = 1000n;
const COUNT_STEP_THOUSANDTHS = 1000n;
const MEASURED_STEP_THOUSANDTHS = 100n;

function toThousandths(quantity: string): bigint {
  const [whole = '0', fraction = ''] = quantity.split('.');
  const paddedFraction = fraction.padEnd(3, '0').slice(0, 3);
  return BigInt(whole) * THOUSANDTHS_PER_UNIT + BigInt(paddedFraction);
}

function fromThousandths(thousandths: bigint): string {
  const whole = thousandths / THOUSANDTHS_PER_UNIT;
  const fraction = thousandths % THOUSANDTHS_PER_UNIT;
  const paddedFraction = fraction.toString().padStart(3, '0');
  return `${whole.toString()}.${paddedFraction}`;
}

export function stepQuantity(
  quantity: string,
  dimension: MeasurementDimension,
  direction: QuantityDirection,
): string {
  const step = dimension === 'count' ? COUNT_STEP_THOUSANDTHS : MEASURED_STEP_THOUSANDTHS;
  const current = toThousandths(quantity);
  const next = current + BigInt(direction) * step;
  const clamped = next < 0n ? 0n : next;
  return fromThousandths(clamped);
}

export function isEmpty(quantity: string): boolean {
  return toThousandths(quantity) === 0n;
}
