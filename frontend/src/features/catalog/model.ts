export const MEASUREMENT_DIMENSIONS = ['mass', 'volume', 'count'] as const;

export type MeasurementDimension = (typeof MEASUREMENT_DIMENSIONS)[number];

export interface MeasurementUnit {
  code: string;
  name: string;
  dimension: MeasurementDimension;
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
