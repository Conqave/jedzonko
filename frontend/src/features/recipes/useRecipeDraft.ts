import { onMounted, ref } from 'vue';
import { useApiAction } from '@/shared/useApiAction';
import { createRecipe, fetchRecipe, fetchRecipeCategories, updateRecipe } from './api';
import { RECIPE_ERROR_MESSAGES } from './errors';
import {
  createEmptyDraft,
  toDraft,
  type RecipeCategory,
  type RecipeDetail,
  type RecipeDraft,
} from './model';

export function useRecipeDraft(recipeId: number | null) {
  const draft = ref<RecipeDraft>(createEmptyDraft());
  const categories = ref<RecipeCategory[]>([]);
  const isLoaded = ref(recipeId === null);
  const { busy, run } = useApiAction(RECIPE_ERROR_MESSAGES);

  async function save(): Promise<RecipeDetail | null> {
    let saved: RecipeDetail | null = null;
    await run(async () => {
      saved =
        recipeId === null
          ? await createRecipe(draft.value)
          : await updateRecipe(recipeId, draft.value);
    });
    return saved;
  }

  onMounted(() => {
    void run(async () => {
      categories.value = await fetchRecipeCategories();
    });
    if (recipeId === null) {
      return;
    }
    void run(async () => {
      const recipe = await fetchRecipe(recipeId);
      draft.value = toDraft(recipe);
      isLoaded.value = true;
    });
  });

  return { draft, categories, isLoaded, busy, save };
}
