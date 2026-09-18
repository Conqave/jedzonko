import { api } from '@/boot/api';
import type { PromotionOffer, StorePromotionCoverage } from './models';

export async function searchPromotions(query: string): Promise<PromotionOffer[]> {
  const response = await api.get<PromotionOffer[]>('/promotions/search/', { params: { query } });
  return response.data;
}

export async function compareStoreCoverage(queries: string[]): Promise<StorePromotionCoverage[]> {
  const response = await api.post<StorePromotionCoverage[]>('/promotions/store-coverage/', {
    queries,
  });
  return response.data;
}
