import { api } from '@/boot/api';
import type { MissingItem, RecipeDetail, RecipeSuggestion, RecipeSummary } from './models';

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
): Promise<MissingItem[]> {
  const response = await api.get<MissingItem[]>(`/recipes/${recipeId}/missing-items/`, {
    params: { household_id: householdId, servings },
  });
  return response.data;
}
