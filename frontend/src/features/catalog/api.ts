import { z } from 'zod';
import { http } from '@/shared/http';
import {
  PRODUCT_INGREDIENT_PROVENANCES,
  PRODUCT_INGREDIENT_STATUSES,
  MEASUREMENT_DIMENSIONS,
  type Ingredient,
  type MeasurementUnit,
  type NewProduct,
  type Product,
  type ProductChanges,
  type ProductIngredientDecision,
  type ProductListing,
  type ProductPackage,
} from './model';

const packageSchema = z
  .object({ quantity: z.string(), unit_code: z.string() })
  .transform((value): ProductPackage => ({ quantity: value.quantity, unitCode: value.unit_code }));

const productSchema = z
  .object({
    id: z.number().int(),
    household_id: z.number().int(),
    name: z.string(),
    default_unit_code: z.string(),
    is_food: z.boolean(),
    package: packageSchema.nullable(),
  })
  .transform((value): Product => ({
    id: value.id,
    householdId: value.household_id,
    name: value.name,
    defaultUnitCode: value.default_unit_code,
    isFood: value.is_food,
    package: value.package,
  }));

const ingredientSchema = z.object({ id: z.number().int(), name: z.string() });

const listingSchema = z
  .object({
    product: productSchema,
    ingredient_id: z.number().int().nullable(),
    ingredient_name: z.string().nullable(),
    open_proposal_count: z.number().int(),
  })
  .transform((value): ProductListing => ({
    product: value.product,
    ingredient:
      value.ingredient_id === null || value.ingredient_name === null
        ? null
        : { id: value.ingredient_id, name: value.ingredient_name },
    openProposalCount: value.open_proposal_count,
  }));

const dateOrNull = z.iso
  .datetime({ offset: true })
  .nullable()
  .transform((value) => (value === null ? null : new Date(value)));

const decisionSchema = z
  .object({
    ingredient: ingredientSchema,
    status: z.enum(PRODUCT_INGREDIENT_STATUSES),
    provenance: z.enum(PRODUCT_INGREDIENT_PROVENANCES),
    model_name: z.string().nullable(),
    proposed_at: dateOrNull,
    decided_at: dateOrNull,
  })
  .transform((value): ProductIngredientDecision => ({
    ingredient: value.ingredient,
    status: value.status,
    provenance: value.provenance,
    modelName: value.model_name,
    proposedAt: value.proposed_at,
    decidedAt: value.decided_at,
  }));

const unitSchema = z.object({
  code: z.string(),
  name: z.string(),
  dimension: z.enum(MEASUREMENT_DIMENSIONS),
});

function toPackagePayload(value: ProductPackage | null) {
  return value === null ? null : { quantity: value.quantity, unit_code: value.unitCode };
}

export async function searchProducts(
  householdId: number,
  search: string,
): Promise<ProductListing[]> {
  const params =
    search === '' ? { household_id: householdId } : { household_id: householdId, search };
  const response = await http.get('/products/', { params });
  return listingSchema.array().parse(response.data);
}

export async function createProduct(product: NewProduct): Promise<Product> {
  const payload = {
    household_id: product.householdId,
    name: product.name,
    default_unit_code: product.defaultUnitCode,
    is_food: product.isFood,
    package: toPackagePayload(product.package),
  };
  const response = await http.post('/products/', payload);
  return productSchema.parse(response.data);
}

export async function updateProduct(productId: number, changes: ProductChanges): Promise<Product> {
  const payload = { name: changes.name, package: toPackagePayload(changes.package) };
  const response = await http.patch(`/products/${productId}/`, payload);
  return productSchema.parse(response.data);
}

export async function fetchProductDecisions(
  productId: number,
): Promise<ProductIngredientDecision[]> {
  const response = await http.get(`/products/${productId}/ingredients/`);
  return decisionSchema.array().parse(response.data);
}

export async function confirmProductIngredient(
  productId: number,
  ingredientId: number,
): Promise<void> {
  await http.post(`/products/${productId}/ingredients/${ingredientId}/confirmation/`);
}

export async function rejectProductIngredient(
  productId: number,
  ingredientId: number,
): Promise<void> {
  await http.post(`/products/${productId}/ingredients/${ingredientId}/rejection/`);
}

const analysisSchema = z.object({ is_proposed: z.boolean() });

export async function analyzeProductIngredient(productId: number): Promise<boolean> {
  const response = await http.post(`/products/${productId}/ingredient-analysis/`);
  const body = analysisSchema.parse(response.data);
  return body.is_proposed;
}

export async function searchIngredients(search: string): Promise<Ingredient[]> {
  const response = await http.get('/ingredients/', { params: { search } });
  return ingredientSchema.array().parse(response.data);
}

export async function fetchMeasurementUnits(): Promise<MeasurementUnit[]> {
  const response = await http.get('/units/');
  return unitSchema.array().parse(response.data);
}
