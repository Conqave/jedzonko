import { onMounted, ref, watch, type Ref } from 'vue';
import { useApiAction } from '@/shared/useApiAction';
import {
  fetchExternalRecipe,
  fetchExternalRecipeNutrition,
  fetchExternalShortfall,
  matchExternalRecipeIngredients,
} from './api';
import { RECIPE_ERROR_MESSAGES } from './errors';
import type { ExternalRecipe, RecipeNutrition, RecipeShortfall } from './model';

export function useExternalRecipe(reference: string, householdId: Ref<number | null>) {
  const recipe = ref<ExternalRecipe | null>(null);
  const shortfall = ref<RecipeShortfall | null>(null);
  const nutrition = ref<RecipeNutrition | null>(null);
  const isMatching = ref(false);
  const { busy, run } = useApiAction(RECIPE_ERROR_MESSAGES);

  async function loadShortfall(): Promise<void> {
    const id = householdId.value;
    shortfall.value = null;
    if (id === null) {
      return;
    }
    await run(async () => {
      shortfall.value = await fetchExternalShortfall(reference, id);
    });
  }

  async function loadNutrition(): Promise<void> {
    await run(async () => {
      nutrition.value = await fetchExternalRecipeNutrition(reference);
    });
  }

  async function matchIngredients(): Promise<void> {
    isMatching.value = true;
    const interpretedCount = ref(0);
    await run(async () => {
      interpretedCount.value = await matchExternalRecipeIngredients(reference);
    });
    isMatching.value = false;
    if (interpretedCount.value > 0) {
      await Promise.all([loadShortfall(), loadNutrition()]);
    }
  }

  onMounted(() => {
    void run(async () => {
      recipe.value = await fetchExternalRecipe(reference);
    });
    void loadShortfall();
    void loadNutrition();
    void matchIngredients();
  });

  watch(householdId, loadShortfall);

  return { recipe, shortfall, nutrition, busy, isMatching, loadShortfall };
}
