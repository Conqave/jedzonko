import { ref } from 'vue';
import { useApiAction } from '@/shared/useApiAction';
import { searchProducts } from './api';
import { CATALOG_ERROR_MESSAGES } from './errors';
import type { Product } from './model';

export function useProductSearch() {
  const products = ref<Product[]>([]);
  const { busy, run } = useApiAction(CATALOG_ERROR_MESSAGES);

  async function search(householdId: number, term: string): Promise<void> {
    await run(async () => {
      const listings = await searchProducts(householdId, term.trim());
      products.value = listings.map((listing) => listing.product);
    });
  }

  return { products, busy, search };
}
