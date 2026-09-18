import { defineStore } from 'pinia';
import { computed, ref } from 'vue';
import * as promotionsApi from './api';
import type { FavouriteShop, Shop } from './models';

export const usePromotionsStore = defineStore('promotions', () => {
  const shops = ref<Shop[]>([]);
  const favourites = ref<FavouriteShop[]>([]);
  const loading = ref(false);
  const saving = ref(false);
  const loaded = ref(false);

  const favouriteSlugs = computed(() => favourites.value.map((shop) => shop.slug));
  const hasFavourites = computed(() => favourites.value.length > 0);

  async function load(): Promise<void> {
    loading.value = true;
    try {
      const [loadedShops, loadedFavourites] = await Promise.all([
        promotionsApi.fetchShops(),
        promotionsApi.fetchFavouriteShops(),
      ]);
      shops.value = loadedShops;
      favourites.value = loadedFavourites;
      loaded.value = true;
    } finally {
      loading.value = false;
    }
  }

  async function saveFavourites(slugs: string[]): Promise<void> {
    saving.value = true;
    try {
      favourites.value = await promotionsApi.saveFavouriteShops(slugs);
    } finally {
      saving.value = false;
    }
  }

  return {
    shops,
    favourites,
    favouriteSlugs,
    hasFavourites,
    loading,
    saving,
    loaded,
    load,
    saveFavourites,
  };
});
