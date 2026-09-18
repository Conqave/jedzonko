import { api } from '@/boot/api';
import type { FavouriteShop, PromotionOffer, Shop, StorePromotionCoverage } from './models';

export async function fetchShops(): Promise<Shop[]> {
  const response = await api.get<Shop[]>('/promotions/shops/');
  return response.data;
}

export async function fetchFavouriteShops(): Promise<FavouriteShop[]> {
  const response = await api.get<FavouriteShop[]>('/promotions/favourite-shops/');
  return response.data;
}

export async function saveFavouriteShops(shops: string[]): Promise<FavouriteShop[]> {
  const response = await api.put<FavouriteShop[]>('/promotions/favourite-shops/', { shops });
  return response.data;
}

export async function searchPromotions(
  query: string,
  shops: string[] = [],
): Promise<PromotionOffer[]> {
  const params: Record<string, string | string[]> = { query };
  if (shops.length > 0) {
    params.shop = shops;
  }
  const response = await api.get<PromotionOffer[]>('/promotions/search/', {
    params,
    paramsSerializer: { indexes: null },
  });
  return response.data;
}

export async function compareStoreCoverage(
  queries: string[],
  shops: string[] = [],
): Promise<StorePromotionCoverage[]> {
  const payload: { queries: string[]; shops?: string[] } = { queries };
  if (shops.length > 0) {
    payload.shops = shops;
  }
  const response = await api.post<StorePromotionCoverage[]>('/promotions/store-coverage/', payload);
  return response.data;
}
