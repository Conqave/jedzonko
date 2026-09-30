import { isBaseUnit, type MeasurementUnit, type ProductChanges } from '@/features/catalog/model';
import { fromThousandths, toThousandths } from '@/shared/decimal';

export interface InventoryItem {
  id: number;
  productId: number;
  productName: string;
  quantity: string;
  unitCode: string;
  minimumQuantity: string | null;
  photoUrl: string | null;
  isBelowMinimum: boolean;
}

export interface NewInventoryItem {
  householdId: number;
  productId: number;
  quantity: string;
  unitCode: string;
  minimumQuantity: string | null;
}

export interface InventoryItemChanges {
  quantity: string;
  unitCode: string;
}

export interface InventoryItemEdit {
  changes: InventoryItemChanges;
  minimumQuantity: string | null;
}

export interface PantryItemEdit {
  product: ProductChanges;
  item: InventoryItemEdit;
}

export interface NewInventoryEntry {
  item: NewInventoryItem;
  photo: File | null;
}

export type QuantityDirection = -1 | 1;

const COUNT_STEP_THOUSANDTHS = 1000n;
const BASE_UNIT_STEP_THOUSANDTHS = 50000n;
const LARGE_UNIT_STEP_THOUSANDTHS = 100n;

function findStep(unit: MeasurementUnit): bigint {
  if (unit.dimension === 'count') {
    return COUNT_STEP_THOUSANDTHS;
  }
  return isBaseUnit(unit) ? BASE_UNIT_STEP_THOUSANDTHS : LARGE_UNIT_STEP_THOUSANDTHS;
}

export function stepQuantity(
  quantity: string,
  unit: MeasurementUnit,
  direction: QuantityDirection,
): string {
  const step = findStep(unit);
  const current = toThousandths(quantity);
  const next = current + BigInt(direction) * step;
  const clamped = next < 0n ? 0n : next;
  return fromThousandths(clamped);
}

export function isEmpty(quantity: string): boolean {
  return toThousandths(quantity) === 0n;
}
