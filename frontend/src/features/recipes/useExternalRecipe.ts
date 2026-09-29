import { onMounted, ref, watch, type Ref } from 'vue';
import { useApiAction } from '@/shared/useApiAction';
import { fetchExternalRecipe, fetchExternalShortfall, matchExternalRecipeIngredients } from './api';
import { RECIPE_ERROR_MESSAGES } from './errors';
import type { ExternalRecipe, RecipeShortfall } from './model';

export function useExternalRecipe(reference: string, householdId: Ref<number | null>) {
  const recipe = ref<ExternalRecipe | null>(null);
  const shortfall = ref<RecipeShortfall | null>(null);
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

  async function matchIngredients(): Promise<void> {
    isMatching.value = true;
    const interpretedCount = ref(0);
    await run(async () => {
      interpretedCount.value = await matchExternalRecipeIngredients(reference);
    });
    isMatching.value = false;
    if (interpretedCount.value > 0) {
      await loadShortfall();
    }
  }

  onMounted(() => {
    void run(async () => {
      recipe.value = await fetchExternalRecipe(reference);
    });
    void loadShortfall();
    void matchIngredients();
  });

  watch(householdId, loadShortfall);

  return { recipe, shortfall, busy, isMatching, loadShortfall };
}
