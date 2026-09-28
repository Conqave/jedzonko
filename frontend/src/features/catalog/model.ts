export type MeasurementDimension = 'mass' | 'volume' | 'count';

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
  ingredient: Ingredient | null;
  openProposalCount: number;
}

export type ProductIngredientStatus = 'proposed' | 'confirmed' | 'rejected';

export type ProductIngredientProvenance = 'manual' | 'model';

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
