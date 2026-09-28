import { onMounted, ref } from 'vue';
import { useApiAction } from '@/shared/useApiAction';
import { confirmPreparation, deleteRecipe, fetchRecipe, fetchShortfall } from './api';
import { RECIPE_ERROR_MESSAGES } from './errors';
import type { RecipeDetail, RecipeShortfall } from './model';

export function useRecipe(recipeId: number) {
  const recipe = ref<RecipeDetail | null>(null);
  const shortfall = ref<RecipeShortfall | null>(null);
  const { busy, run } = useApiAction(RECIPE_ERROR_MESSAGES);

  function loadShortfall(householdId: number, servings: number): Promise<boolean> {
    return run(async () => {
      shortfall.value = await fetchShortfall(recipeId, householdId, servings);
    });
  }

  function confirm(householdId: number, servings: number): Promise<boolean> {
    return run(async () => {
      await confirmPreparation(recipeId, householdId, servings);
      shortfall.value = await fetchShortfall(recipeId, householdId, servings);
    });
  }

  function remove(): Promise<boolean> {
    return run(() => deleteRecipe(recipeId));
  }

  onMounted(() => {
    void run(async () => {
      recipe.value = await fetchRecipe(recipeId);
    });
  });

  return { recipe, shortfall, busy, loadShortfall, confirm, remove };
}
