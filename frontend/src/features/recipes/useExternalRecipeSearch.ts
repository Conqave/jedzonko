import { ref } from 'vue';
import { useApiAction } from '@/shared/useApiAction';
import { fetchExternalSuggestions, searchExternalRecipes } from './api';
import { RECIPE_ERROR_MESSAGES } from './errors';
import type { ExternalRecipePage } from './model';

type SearchMode = { kind: 'query'; query: string } | { kind: 'pantry' };

export function useExternalRecipeSearch() {
  const page = ref<ExternalRecipePage | null>(null);
  const pantryIngredientNames = ref<string[]>([]);
  const pantryItemCount = ref(0);
  const mode = ref<SearchMode>({ kind: 'query', query: '' });
  const { busy, run } = useApiAction(RECIPE_ERROR_MESSAGES);

  async function loadPage(householdId: number, pageIndex: number): Promise<void> {
    const current = mode.value;
    await run(async () => {
      if (current.kind === 'query') {
        page.value = await searchExternalRecipes(householdId, current.query, pageIndex);
        pantryIngredientNames.value = [];
        pantryItemCount.value = 0;
        return;
      }
      const suggestions = await fetchExternalSuggestions(householdId, pageIndex);
      page.value = suggestions.page;
      pantryIngredientNames.value = suggestions.ingredientNames;
      pantryItemCount.value = suggestions.inventoryItemCount;
    });
  }

  function searchByQuery(householdId: number, query: string): Promise<void> {
    mode.value = { kind: 'query', query: query.trim() };
    return loadPage(householdId, 0);
  }

  function searchByPantry(householdId: number): Promise<void> {
    mode.value = { kind: 'pantry' };
    return loadPage(householdId, 0);
  }

  return {
    page,
    pantryIngredientNames,
    pantryItemCount,
    busy,
    loadPage,
    searchByQuery,
    searchByPantry,
  };
}
