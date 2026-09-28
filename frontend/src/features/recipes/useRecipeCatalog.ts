import { ref, watch, type Ref } from 'vue';
import { useApiAction } from '@/shared/useApiAction';
import { fetchRecipes, fetchSuggestions } from './api';
import { RECIPE_ERROR_MESSAGES } from './errors';
import type { RecipeSuggestion, RecipeSummary } from './model';

export function useRecipeCatalog(householdId: Ref<number | null>) {
  const recipes = ref<RecipeSummary[]>([]);
  const suggestions = ref<RecipeSuggestion[]>([]);
  const { busy, run } = useApiAction(RECIPE_ERROR_MESSAGES);

  async function load(): Promise<void> {
    const id = householdId.value;
    await run(async () => {
      recipes.value = await fetchRecipes();
      suggestions.value = id === null ? [] : await fetchSuggestions(id);
    });
  }

  watch(householdId, load, { immediate: true });

  return { recipes, suggestions, busy };
}
