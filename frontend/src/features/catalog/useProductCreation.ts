import { useApiAction } from '@/shared/useApiAction';
import { createProduct } from './api';
import { CATALOG_ERROR_MESSAGES } from './errors';
import type { NewProduct, Product } from './model';

export function useProductCreation() {
  const { busy, run } = useApiAction(CATALOG_ERROR_MESSAGES);

  async function create(product: NewProduct): Promise<Product | null> {
    let created: Product | null = null;
    await run(async () => {
      created = await createProduct(product);
    });
    return created;
  }

  return { busy, create };
}
