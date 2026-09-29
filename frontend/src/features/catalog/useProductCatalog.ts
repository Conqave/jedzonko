import { ref, watch, type Ref } from 'vue';
import { useApiAction } from '@/shared/useApiAction';
import { deleteProduct, searchProducts, updateProduct } from './api';
import { CATALOG_ERROR_MESSAGES } from './errors';
import type { ProductChanges, ProductListing } from './model';

export function useProductCatalog(householdId: Ref<number | null>) {
  const listings = ref<ProductListing[]>([]);
  const search = ref('');
  const { busy, run } = useApiAction(CATALOG_ERROR_MESSAGES);

  async function load(): Promise<void> {
    const id = householdId.value;
    if (id === null) {
      listings.value = [];
      return;
    }
    await run(async () => {
      listings.value = await searchProducts(id, search.value.trim());
    });
  }

  function update(productId: number, changes: ProductChanges): Promise<boolean> {
    return run(async () => {
      const product = await updateProduct(productId, changes);
      listings.value = listings.value.map((listing) =>
        listing.product.id === product.id ? { ...listing, product } : listing,
      );
    });
  }

  function remove(productId: number): Promise<boolean> {
    return run(async () => {
      await deleteProduct(productId);
      listings.value = listings.value.filter((listing) => listing.product.id !== productId);
    });
  }

  watch([householdId, search], load, { immediate: true });

  return { listings, search, busy, load, update, remove };
}
