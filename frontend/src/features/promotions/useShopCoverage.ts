import { computed, ref } from 'vue';
import { useApiAction } from '@/shared/useApiAction';
import { compareShopCoverage } from './api';
import { PROMOTION_ERROR_MESSAGES } from './errors';
import { findBestCoverage, type ShopCoverage } from './model';

export function useShopCoverage() {
  const coverage = ref<ShopCoverage[]>([]);
  const comparedQueries = ref<string[]>([]);
  const hasCompared = ref(false);
  const { busy, run } = useApiAction(PROMOTION_ERROR_MESSAGES);

  const bestShops = computed(() => findBestCoverage(coverage.value));

  async function compare(queries: string[], shopSlugs: string[]): Promise<void> {
    const requested = [...queries];
    await run(async () => {
      coverage.value = await compareShopCoverage(requested, shopSlugs);
      comparedQueries.value = requested;
      hasCompared.value = true;
    });
  }

  return { coverage, comparedQueries, bestShops, hasCompared, busy, compare };
}
