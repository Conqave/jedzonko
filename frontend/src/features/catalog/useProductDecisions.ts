import { onMounted, ref } from 'vue';
import { useApiAction } from '@/shared/useApiAction';
import { confirmProductIngredient, fetchProductDecisions, rejectProductIngredient } from './api';
import { CATALOG_ERROR_MESSAGES } from './errors';
import type { ProductIngredientDecision } from './model';

export function useProductDecisions(productId: number) {
  const decisions = ref<ProductIngredientDecision[]>([]);
  const { busy, run } = useApiAction(CATALOG_ERROR_MESSAGES);

  async function reload(): Promise<void> {
    decisions.value = await fetchProductDecisions(productId);
  }

  function confirm(ingredientId: number): Promise<boolean> {
    return run(async () => {
      await confirmProductIngredient(productId, ingredientId);
      await reload();
    });
  }

  function reject(ingredientId: number): Promise<boolean> {
    return run(async () => {
      await rejectProductIngredient(productId, ingredientId);
      await reload();
    });
  }

  onMounted(() => {
    void run(reload);
  });

  return { decisions, busy, confirm, reject };
}
