import { ref } from 'vue';
import { useApiAction } from '@/shared/useApiAction';
import { searchIngredients } from './api';
import { CATALOG_ERROR_MESSAGES } from './errors';
import type { Ingredient } from './model';

export function useIngredientSearch() {
  const ingredients = ref<Ingredient[]>([]);
  const { busy, run } = useApiAction(CATALOG_ERROR_MESSAGES);

  async function search(term: string): Promise<void> {
    const trimmed = term.trim();
    if (trimmed === '') {
      ingredients.value = [];
      return;
    }
    await run(async () => {
      ingredients.value = await searchIngredients(trimmed);
    });
  }

  return { ingredients, busy, search };
}
