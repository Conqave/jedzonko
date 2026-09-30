import { toDecimalText, toThousandths } from '@/shared/decimal';
import { formatQuantity } from '@/shared/formatQuantity';

export const MEASUREMENT_DIMENSIONS = ['mass', 'volume', 'count'] as const;

export type MeasurementDimension = (typeof MEASUREMENT_DIMENSIONS)[number];

export interface MeasurementUnit {
  code: string;
  name: string;
  dimension: MeasurementDimension;
  factorToBase: string;
}

const BASE_FACTOR_THOUSANDTHS = 1000n;

export function isBaseUnit(unit: MeasurementUnit): boolean {
  return toThousandths(unit.factorToBase) === BASE_FACTOR_THOUSANDTHS;
}

export interface ProductPackage {
  quantity: string;
  unitCode: string;
}

export interface Product {
  id: number;
  householdId: number;
  name: string;
  defaultUnitCode: string;
  isFood: boolean;
  package: ProductPackage | null;
}

export interface Ingredient {
  id: number;
  name: string;
}

export const CALORIE_PROVENANCES = ['manual', 'reference'] as const;

export type CalorieProvenance = (typeof CALORIE_PROVENANCES)[number];

export interface TagCalories {
  kcalPer100g: string;
  provenance: CalorieProvenance;
  referenceUrl: string | null;
}

export function describeTagCalories(calories: TagCalories | null): string {
  if (calories === null) {
    return 'brak kcal';
  }
  return `${formatQuantity(calories.kcalPer100g)} kcal/100 g`;
}

const KCAL_INPUT = /^\d{1,3}([.,]\d)?$/;

export function isKcalInput(value: string): boolean {
  return KCAL_INPUT.test(value.trim());
}

export function toKcalPayload(value: string): string | null {
  const trimmed = value.trim();
  return trimmed === '' ? null : toDecimalText(trimmed);
}

export interface ProductListing {
  product: Product;
  tags: Ingredient[];
  openProposalCount: number;
}

export const PRODUCT_INGREDIENT_STATUSES = ['proposed', 'confirmed', 'rejected'] as const;

export type ProductIngredientStatus = (typeof PRODUCT_INGREDIENT_STATUSES)[number];

export const PRODUCT_INGREDIENT_PROVENANCES = ['manual', 'model'] as const;

export type ProductIngredientProvenance = (typeof PRODUCT_INGREDIENT_PROVENANCES)[number];

export interface ProductIngredientDecision {
  ingredient: Ingredient;
  calories: TagCalories | null;
  status: ProductIngredientStatus;
  provenance: ProductIngredientProvenance;
  modelName: string | null;
  proposedAt: Date | null;
  decidedAt: Date | null;
}

export interface NewProduct {
  householdId: number;
  name: string;
  defaultUnitCode: string;
  isFood: boolean;
  package: ProductPackage | null;
}

export interface ProductChanges {
  name: string;
  package: ProductPackage | null;
}

export function normalizePackage(value: ProductPackage | null): ProductPackage | null {
  return value === null ? null : { ...value, quantity: toDecimalText(value.quantity) };
}

export function formatPackage(value: ProductPackage | null): ProductPackage | null {
  return value === null ? null : { ...value, quantity: formatQuantity(value.quantity) };
}
