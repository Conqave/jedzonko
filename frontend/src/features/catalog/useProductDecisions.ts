import { computed, onMounted, ref } from 'vue';
import { useApiAction } from '@/shared/useApiAction';
import {
  analyzeProductIngredient,
  confirmProductIngredient,
  fetchProductDecisions,
  rejectProductIngredient,
} from './api';
import { CATALOG_ERROR_MESSAGES } from './errors';
import type { ProductIngredientDecision } from './model';

export function useProductDecisions(productId: number) {
  const decisions = ref<ProductIngredientDecision[]>([]);
  const isAnalyzing = ref(false);
  const { busy, run } = useApiAction(CATALOG_ERROR_MESSAGES);

  const hasConfirmed = computed(() =>
    decisions.value.some((decision) => decision.status === 'confirmed'),
  );

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

  async function analyze(): Promise<boolean> {
    isAnalyzing.value = true;
    const isProposed = ref(false);
    await run(async () => {
      isProposed.value = await analyzeProductIngredient(productId);
      await reload();
    });
    isAnalyzing.value = false;
    return isProposed.value;
  }

  onMounted(() => {
    void run(reload);
  });

  return { decisions, hasConfirmed, busy, isAnalyzing, confirm, reject, analyze };
}
