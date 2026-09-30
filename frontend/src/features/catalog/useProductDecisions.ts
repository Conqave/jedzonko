import { computed, onMounted, ref } from 'vue';
import { useApiAction } from '@/shared/useApiAction';
import {
  analyzeProductIngredient,
  confirmProductIngredient,
  deleteProductIngredient,
  deleteRejectedProductIngredients,
  fetchProductDecisions,
  rejectProductIngredient,
  setTagCalories,
  setTagDensity,
  setTagPieceWeight,
} from './api';
import { CATALOG_ERROR_MESSAGES } from './errors';
import { groupProductDecisions, type ProductIngredientDecision } from './model';

export function useProductDecisions(productId: number) {
  const decisions = ref<ProductIngredientDecision[]>([]);
  const groups = computed(() => groupProductDecisions(decisions.value));
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

  function forget(ingredientId: number): Promise<boolean> {
    return run(async () => {
      await deleteProductIngredient(productId, ingredientId);
      await reload();
    });
  }

  function forgetRejections(): Promise<boolean> {
    return run(async () => {
      await deleteRejectedProductIngredients(productId);
      await reload();
    });
  }

  function setCalories(ingredientId: number, kcalPer100g: string | null): Promise<boolean> {
    return run(async () => {
      await setTagCalories(ingredientId, kcalPer100g);
      await reload();
    });
  }

  function setPieceWeight(ingredientId: number, gramsPerPiece: string | null): Promise<boolean> {
    return run(async () => {
      await setTagPieceWeight(ingredientId, gramsPerPiece);
      await reload();
    });
  }

  function setDensity(ingredientId: number, gramsPerMl: string | null): Promise<boolean> {
    return run(async () => {
      await setTagDensity(ingredientId, gramsPerMl);
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

  return {
    groups,
    busy,
    isAnalyzing,
    confirm,
    reject,
    forget,
    forgetRejections,
    setCalories,
    setPieceWeight,
    setDensity,
    analyze,
  };
}
