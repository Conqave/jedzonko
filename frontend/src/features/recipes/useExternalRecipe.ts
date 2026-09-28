import { onMounted, ref, watch, type Ref } from 'vue';
import { useApiAction } from '@/shared/useApiAction';
import { fetchExternalRecipe, fetchExternalShortfall } from './api';
import { RECIPE_ERROR_MESSAGES } from './errors';
import type { ExternalRecipe, RecipeShortfall } from './model';

export function useExternalRecipe(reference: string, householdId: Ref<number | null>) {
  const recipe = ref<ExternalRecipe | null>(null);
  const shortfall = ref<RecipeShortfall | null>(null);
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

  onMounted(() => {
    void run(async () => {
      recipe.value = await fetchExternalRecipe(reference);
    });
  });

  watch(householdId, loadShortfall, { immediate: true });

  return { recipe, shortfall, busy, loadShortfall };
}
