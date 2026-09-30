import { describeKcalPer100g } from '@/shared/calories';
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

export const FACT_PROVENANCES = ['manual', 'reference'] as const;

export type FactProvenance = (typeof FACT_PROVENANCES)[number];

export interface TagFactSource {
  provenance: FactProvenance;
  referenceUrl: string | null;
}

export interface TagCalories extends TagFactSource {
  kcalPer100g: string;
}

export interface TagPieceWeight extends TagFactSource {
  gramsPerPiece: string;
}

export interface TagDensity extends TagFactSource {
  gramsPerMl: string;
}

export function describeTagCalories(calories: TagCalories | null): string {
  if (calories === null) {
    return 'brak kcal';
  }
  return describeKcalPer100g(calories.kcalPer100g);
}

export function describeTagPieceWeight(pieceWeight: TagPieceWeight | null): string {
  if (pieceWeight === null) {
    return 'brak wagi sztuki';
  }
  return `${formatQuantity(pieceWeight.gramsPerPiece)} g/szt.`;
}

export function describeTagDensity(density: TagDensity | null): string {
  if (density === null) {
    return 'brak gęstości';
  }
  return `${formatQuantity(density.gramsPerMl)} g/ml`;
}

const KCAL_INPUT = /^\d{1,3}([.,]\d)?$/;
const PIECE_WEIGHT_INPUT = /^\d{1,5}([.,]\d)?$/;
const DENSITY_INPUT = /^\d([.,]\d{1,3})?$/;
const MAX_KCAL_PER_100G = 900;
const MAX_GRAMS_PER_PIECE = 10000;
const MAX_GRAMS_PER_ML = 3;

function isDecimalWithin(
  value: string,
  pattern: RegExp,
  isPositive: boolean,
  max: number,
): boolean {
  const trimmed = value.trim();
  if (!pattern.test(trimmed)) {
    return false;
  }
  const amount = Number(toDecimalText(trimmed));
  const isAboveMinimum = isPositive ? amount > 0 : amount >= 0;
  return isAboveMinimum && amount <= max;
}

export function isKcalInput(value: string): boolean {
  return isDecimalWithin(value, KCAL_INPUT, false, MAX_KCAL_PER_100G);
}

export function isPieceWeightInput(value: string): boolean {
  return isDecimalWithin(value, PIECE_WEIGHT_INPUT, true, MAX_GRAMS_PER_PIECE);
}

export function isDensityInput(value: string): boolean {
  return isDecimalWithin(value, DENSITY_INPUT, true, MAX_GRAMS_PER_ML);
}

export function toOptionalDecimalPayload(value: string): string | null {
  const trimmed = value.trim();
  return trimmed === '' ? null : toDecimalText(trimmed);
}

export interface ProductListing {
  product: Product;
  tags: Ingredient[];
  openProposalCount: number;
}

export const TAG_FILTERS = ['all', 'tagged', 'untagged'] as const;

export type TagFilter = (typeof TAG_FILTERS)[number];

export const TAG_FILTER_LABELS: Readonly<Record<TagFilter, string>> = {
  all: 'Wszystkie',
  tagged: 'Z tagiem',
  untagged: 'Bez tagu',
};

export function matchesTagFilter(filter: TagFilter, tagNames: readonly string[]): boolean {
  if (filter === 'all') {
    return true;
  }
  const isTagged = tagNames.length > 0;
  return filter === 'tagged' ? isTagged : !isTagged;
}

export const PRODUCT_INGREDIENT_STATUSES = ['proposed', 'confirmed', 'rejected'] as const;

export type ProductIngredientStatus = (typeof PRODUCT_INGREDIENT_STATUSES)[number];

export const PRODUCT_INGREDIENT_PROVENANCES = ['manual', 'model'] as const;

export type ProductIngredientProvenance = (typeof PRODUCT_INGREDIENT_PROVENANCES)[number];

export interface ProductIngredientDecision {
  ingredient: Ingredient;
  calories: TagCalories | null;
  pieceWeight: TagPieceWeight | null;
  density: TagDensity | null;
  status: ProductIngredientStatus;
  provenance: ProductIngredientProvenance;
  modelName: string | null;
  proposedAt: Date | null;
  decidedAt: Date | null;
}

export interface ProductDecisionGroups {
  tags: ProductIngredientDecision[];
  proposals: ProductIngredientDecision[];
  rejections: ProductIngredientDecision[];
}

export function groupProductDecisions(
  decisions: readonly ProductIngredientDecision[],
): ProductDecisionGroups {
  return {
    tags: decisions.filter((decision) => decision.status === 'confirmed'),
    proposals: decisions.filter((decision) => decision.status === 'proposed'),
    rejections: decisions.filter((decision) => decision.status === 'rejected'),
  };
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
