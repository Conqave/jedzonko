import { api } from '@/boot/api';
import type {
  ExternalRecipe,
  ExternalRecipePage,
  ExternalRecipeSuggestionPage,
  RecipeDetail,
  RecipeInput,
  RecipeShortfall,
  RecipeSuggestion,
  RecipeSummary,
} from './models';

export async function fetchRecipes(): Promise<RecipeSummary[]> {
  const response = await api.get<RecipeSummary[]>('/recipes/');
  return response.data;
}

export async function fetchRecipe(recipeId: number): Promise<RecipeDetail> {
  const response = await api.get<RecipeDetail>(`/recipes/${recipeId}/`);
  return response.data;
}

export async function fetchSuggestions(householdId: number): Promise<RecipeSuggestion[]> {
  const response = await api.get<RecipeSuggestion[]>('/recipes/suggestions/', {
    params: { household_id: householdId },
  });
  return response.data;
}

export async function fetchMissingItems(
  recipeId: number,
  householdId: number,
  servings: number,
): Promise<RecipeShortfall> {
  const response = await api.get<RecipeShortfall>(`/recipes/${recipeId}/missing-items/`, {
    params: { household_id: householdId, servings },
  });
  return response.data;
}

export async function searchExternalRecipes(
  query: string,
  page: number,
): Promise<ExternalRecipePage> {
  const response = await api.get<ExternalRecipePage>('/recipes/external/', {
    params: { query, page },
  });
  return response.data;
}

export async function fetchExternalSuggestions(
  householdId: number,
  page: number,
): Promise<ExternalRecipeSuggestionPage> {
  const response = await api.get<ExternalRecipeSuggestionPage>('/recipes/external/suggestions/', {
    params: { household_id: householdId, page },
  });
  return response.data;
}

export async function fetchExternalRecipe(reference: string): Promise<ExternalRecipe> {
  const response = await api.get<ExternalRecipe>(`/recipes/external/${reference}/`);
  return response.data;
}

export async function createRecipe(recipe: RecipeInput): Promise<RecipeDetail> {
  const response = await api.post<RecipeDetail>('/recipes/', recipe);
  return response.data;
}

export async function updateRecipe(recipeId: number, recipe: RecipeInput): Promise<RecipeDetail> {
  const response = await api.put<RecipeDetail>(`/recipes/${recipeId}/`, recipe);
  return response.data;
}

export async function deleteRecipe(recipeId: number): Promise<void> {
  await api.delete(`/recipes/${recipeId}/`);
}

export async function confirmPreparation(
  recipeId: number,
  householdId: number,
  servings: number,
): Promise<void> {
  await api.post(`/recipes/${recipeId}/confirm-preparation/`, {
    household_id: householdId,
    servings,
  });
}
