import { computed, ref } from 'vue';
import { useApiAction } from '@/shared/useApiAction';
import { fetchFavouriteShopSlugs, fetchShops, saveFavouriteShopSlugs } from './api';
import { PROMOTION_ERROR_MESSAGES } from './errors';
import type { PromotionShop } from './model';

export function useFavouriteShops() {
  const shops = ref<PromotionShop[]>([]);
  const favouriteSlugs = ref<string[]>([]);
  const isLoaded = ref(false);
  const { busy, run } = useApiAction(PROMOTION_ERROR_MESSAGES);

  const favouriteShops = computed(() =>
    shops.value.filter((shop) => favouriteSlugs.value.includes(shop.slug)),
  );

  function findShopNames(slugs: string[]): string[] {
    return slugs.map((slug) => shops.value.find((shop) => shop.slug === slug)?.name ?? slug);
  }

  async function load(): Promise<void> {
    await run(async () => {
      const loadedShops = await fetchShops();
      const loadedSlugs = await fetchFavouriteShopSlugs();
      shops.value = loadedShops;
      favouriteSlugs.value = loadedSlugs;
      isLoaded.value = true;
    });
  }

  function saveFavourites(slugs: string[]): Promise<boolean> {
    return run(async () => {
      favouriteSlugs.value = await saveFavouriteShopSlugs(slugs);
    });
  }

  return {
    shops,
    favouriteSlugs,
    favouriteShops,
    isLoaded,
    busy,
    findShopNames,
    load,
    saveFavourites,
  };
}
