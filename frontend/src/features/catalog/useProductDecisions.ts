import { onMounted, ref } from 'vue';
import { useApiAction } from '@/shared/useApiAction';
import {
  analyzeProductIngredient,
  confirmProductIngredient,
  fetchProductDecisions,
  rejectProductIngredient,
  setTagCalories,
} from './api';
import { CATALOG_ERROR_MESSAGES } from './errors';
import type { ProductIngredientDecision } from './model';

export function useProductDecisions(productId: number) {
  const decisions = ref<ProductIngredientDecision[]>([]);
  const isAnalyzing = ref(false);
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

  function setCalories(ingredientId: number, kcalPer100g: string | null): Promise<boolean> {
    return run(async () => {
      await setTagCalories(ingredientId, kcalPer100g);
      await reload();
    });
  }

  async function analyze(): Promise<number> {
    isAnalyzing.value = true;
    let proposedCount = 0;
    try {
      await run(async () => {
        proposedCount = await analyzeProductIngredient(productId);
        await reload();
      });
    } finally {
      isAnalyzing.value = false;
    }
    return proposedCount;
  }

  onMounted(() => {
    void run(reload);
  });

  return { decisions, busy, isAnalyzing, confirm, reject, setCalories, analyze };
}
