import { z } from 'zod';
import { http } from '@/shared/http';
import {
  RECIPE_DIFFICULTIES,
  type ExternalRecipe,
  type ExternalRecipeMatch,
  type ExternalRecipePage,
  type ExternalRecipeSuggestions,
  type ExternalRecipeSummary,
  type RecipeCategory,
  type RecipeDetail,
  type RecipeDraft,
  type RecipeShortfall,
  type RecipeSuggestion,
  type RecipeSummary,
} from './model';

const difficultySchema = z.enum(RECIPE_DIFFICULTIES);

const categorySchema = z.object({ id: z.number().int(), name: z.string() });

const summaryFields = {
  id: z.number().int(),
  name: z.string(),
  description: z.string(),
  servings: z.number().int(),
  preparation_time_minutes: z.number().int(),
  cooking_time_minutes: z.number().int(),
  difficulty: difficultySchema,
  category: categorySchema.nullable(),
  tags: z.array(z.string()),
  image_url: z.string().nullable(),
  author_username: z.string(),
};

type SummaryDto = z.infer<z.ZodObject<typeof summaryFields>>;

function toSummary(value: SummaryDto): RecipeSummary {
  return {
    id: value.id,
    name: value.name,
    description: value.description,
    servings: value.servings,
    preparationTimeMinutes: value.preparation_time_minutes,
    cookingTimeMinutes: value.cooking_time_minutes,
    difficulty: value.difficulty,
    category: value.category,
    tags: value.tags,
    imageUrl: value.image_url,
    authorUsername: value.author_username,
  };
}

const summarySchema = z.object(summaryFields).transform(toSummary);

const detailSchema = z
  .object({
    ...summaryFields,
    steps: z.array(z.object({ position: z.number().int(), text: z.string() })),
    ingredients: z.array(
      z.object({
        name: z.string(),
        ingredient_id: z.number().int().nullable(),
        quantity: z.string(),
        unit_code: z.string(),
      }),
    ),
  })
  .transform((value): RecipeDetail => ({
    ...toSummary(value),
    steps: value.steps,
    ingredients: value.ingredients.map((line) => ({
      name: line.name,
      ingredientId: line.ingredient_id,
      quantity: line.quantity,
      unitCode: line.unit_code,
    })),
  }));

const shortfallSchema = z
  .object({
    missing_items: z.array(
      z.object({
        name: z.string(),
        amount: z.string().nullable(),
        unit_code: z.string().nullable(),
      }),
    ),
    required_item_count: z.number().int(),
    available_item_count: z.number().int(),
    unmeasured_ingredients: z.array(z.string()),
    is_ready: z.boolean(),
  })
  .transform((value): RecipeShortfall => ({
    missingItems: value.missing_items.map((item) => ({
      name: item.name,
      amount: item.amount,
      unitCode: item.unit_code,
    })),
    requiredItemCount: value.required_item_count,
    availableItemCount: value.available_item_count,
    unmeasuredIngredients: value.unmeasured_ingredients,
    isReady: value.is_ready,
  }));

const suggestionSchema = z
  .object({ recipe_id: z.number().int(), recipe_name: z.string(), shortfall: shortfallSchema })
  .transform((value): RecipeSuggestion => ({
    recipeId: value.recipe_id,
    recipeName: value.recipe_name,
    shortfall: value.shortfall,
  }));

const externalSummaryFields = {
  source_name: z.string(),
  source_url: z.string(),
  reference: z.string(),
  name: z.string(),
  description: z.string(),
  image_url: z.string().nullable(),
  yield_label: z.string(),
  total_time_minutes: z.number().int().nullable(),
  tags: z.array(z.string()),
};

type ExternalSummaryDto = z.infer<z.ZodObject<typeof externalSummaryFields>>;

function toExternalSummary(value: ExternalSummaryDto): ExternalRecipeSummary {
  return {
    sourceName: value.source_name,
    sourceUrl: value.source_url,
    reference: value.reference,
    name: value.name,
    description: value.description,
    imageUrl: value.image_url,
    yieldLabel: value.yield_label,
    totalTimeMinutes: value.total_time_minutes,
    tags: value.tags,
  };
}

const externalMatchSchema = z
  .object({ ...externalSummaryFields, matched_product_names: z.array(z.string()) })
  .transform((value): ExternalRecipeMatch => ({
    ...toExternalSummary(value),
    matchedProductNames: value.matched_product_names,
  }));

const externalPageSchema = z
  .object({
    recipes: z.array(externalMatchSchema),
    page: z.number().int(),
    page_size: z.number().int(),
    total_count: z.number().int(),
    total_pages: z.number().int(),
  })
  .transform((value): ExternalRecipePage => ({
    recipes: value.recipes,
    page: value.page,
    totalPages: value.total_pages,
    totalCount: value.total_count,
  }));

const externalSuggestionsSchema = z
  .object({
    page: externalPageSchema,
    ingredient_names: z.array(z.string()),
    inventory_item_count: z.number().int(),
  })
  .transform((value): ExternalRecipeSuggestions => ({
    page: value.page,
    ingredientNames: value.ingredient_names,
    inventoryItemCount: value.inventory_item_count,
  }));

const externalRecipeSchema = z
  .object({
    ...externalSummaryFields,
    preparation_time_minutes: z.number().int().nullable(),
    cooking_time_minutes: z.number().int().nullable(),
    steps: z.array(z.string()),
    ingredients: z.array(
      z.object({
        source_text: z.string(),
        name: z.string(),
        quantity: z.string().nullable(),
        unit_code: z.string().nullable(),
      }),
    ),
  })
  .transform((value): ExternalRecipe => ({
    ...toExternalSummary(value),
    preparationTimeMinutes: value.preparation_time_minutes,
    cookingTimeMinutes: value.cooking_time_minutes,
    steps: value.steps,
    ingredients: value.ingredients.map((line) => ({
      sourceText: line.source_text,
      name: line.name,
      quantity: line.quantity,
      unitCode: line.unit_code,
    })),
  }));

function toDraftPayload(draft: RecipeDraft) {
  return {
    name: draft.name,
    description: draft.description,
    servings: draft.servings,
    preparation_time_minutes: draft.preparationTimeMinutes,
    cooking_time_minutes: draft.cookingTimeMinutes,
    difficulty: draft.difficulty,
    category_id: draft.categoryId,
    tag_names: draft.tagNames,
    steps: draft.steps.map((text, index) => ({ position: index + 1, text })),
    ingredients: draft.ingredients.map((line) => ({
      name: line.name,
      quantity: line.quantity,
      unit_code: line.unitCode,
    })),
  };
}

export async function fetchRecipes(): Promise<RecipeSummary[]> {
  const response = await http.get('/recipes/');
  return summarySchema.array().parse(response.data);
}

export async function fetchRecipeCategories(): Promise<RecipeCategory[]> {
  const response = await http.get('/recipes/categories/');
  return categorySchema.array().parse(response.data);
}

export async function fetchRecipe(recipeId: number): Promise<RecipeDetail> {
  const response = await http.get(`/recipes/${recipeId}/`);
  return detailSchema.parse(response.data);
}

export async function createRecipe(draft: RecipeDraft): Promise<RecipeDetail> {
  const payload = toDraftPayload(draft);
  const response = await http.post('/recipes/', payload);
  return detailSchema.parse(response.data);
}

export async function updateRecipe(recipeId: number, draft: RecipeDraft): Promise<RecipeDetail> {
  const payload = toDraftPayload(draft);
  const response = await http.put(`/recipes/${recipeId}/`, payload);
  return detailSchema.parse(response.data);
}

export async function deleteRecipe(recipeId: number): Promise<void> {
  await http.delete(`/recipes/${recipeId}/`);
}

export async function fetchSuggestions(householdId: number): Promise<RecipeSuggestion[]> {
  const response = await http.get('/recipes/suggestions/', {
    params: { household_id: householdId },
  });
  return suggestionSchema.array().parse(response.data);
}

export async function fetchShortfall(
  recipeId: number,
  householdId: number,
  servings: number,
): Promise<RecipeShortfall> {
  const params = { household_id: householdId, servings };
  const response = await http.get(`/recipes/${recipeId}/missing-items/`, { params });
  return shortfallSchema.parse(response.data);
}

export async function confirmPreparation(
  recipeId: number,
  householdId: number,
  servings: number,
): Promise<void> {
  const payload = { household_id: householdId, servings };
  await http.post(`/recipes/${recipeId}/confirm-preparation/`, payload);
}

export async function searchExternalRecipes(
  householdId: number,
  query: string,
  page: number,
): Promise<ExternalRecipePage> {
  const params = { household_id: householdId, query, page };
  const response = await http.get('/recipes/external/', { params });
  return externalPageSchema.parse(response.data);
}

export async function fetchExternalSuggestions(
  householdId: number,
  page: number,
): Promise<ExternalRecipeSuggestions> {
  const params = { household_id: householdId, page };
  const response = await http.get('/recipes/external/suggestions/', { params });
  return externalSuggestionsSchema.parse(response.data);
}

export async function fetchExternalRecipe(reference: string): Promise<ExternalRecipe> {
  const response = await http.get(`/recipes/external/${reference}/`);
  return externalRecipeSchema.parse(response.data);
}

export async function fetchExternalShortfall(
  reference: string,
  householdId: number,
): Promise<RecipeShortfall> {
  const params = { household_id: householdId };
  const response = await http.get(`/recipes/external/${reference}/missing-items/`, { params });
  return shortfallSchema.parse(response.data);
}

const matchingSchema = z.object({ interpreted_line_count: z.number().int() });

export async function matchExternalRecipeIngredients(reference: string): Promise<number> {
  const response = await http.post(`/recipes/external/${reference}/ingredient-matching/`);
  const body = matchingSchema.parse(response.data);
  return body.interpreted_line_count;
}
