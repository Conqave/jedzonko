import { ref } from 'vue';
import { useApiAction } from '@/shared/useApiAction';
import { addRecipeItems, fetchShoppingLists } from './api';
import { SHOPPING_ERROR_MESSAGES } from './errors';
import { orderPrimaryFirst, type RecipeShoppingSource, type ShoppingList } from './model';

export function useRecipeShopping() {
  const lists = ref<ShoppingList[]>([]);
  const { busy, run } = useApiAction(SHOPPING_ERROR_MESSAGES);

  function loadLists(householdId: number): Promise<boolean> {
    return run(async () => {
      const found = await fetchShoppingLists(householdId);
      lists.value = orderPrimaryFirst(found);
    });
  }

  function addToList(listId: number, source: RecipeShoppingSource): Promise<boolean> {
    return run(async () => {
      await addRecipeItems(listId, source);
    });
  }

  return { lists, busy, loadLists, addToList };
}
