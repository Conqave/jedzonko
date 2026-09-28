import { z } from 'zod';
import { http } from '@/shared/http';
import type { PromotionOffer, PromotionShop, ShopCoverage } from './model';

const shopSchema = z.object({ name: z.string(), slug: z.string(), url: z.string() });

const favouriteShopSchema = z.object({ name: z.string(), slug: z.string() });

const offerSchema = z
  .object({
    provider_offer_id: z.string().nullable(),
    name: z.string(),
    shop_name: z.string(),
    shop_slug: z.string(),
    shop_url: z.string(),
    image_url: z.string(),
    product_brand_name: z.string().nullable(),
    price: z.string().nullable(),
    leaflet_url: z.string(),
    page_number: z.number().int(),
    valid_from: z.iso.date(),
    valid_until: z.iso.date(),
  })
  .transform((offer): PromotionOffer => ({
    providerOfferId: offer.provider_offer_id,
    name: offer.name,
    shopName: offer.shop_name,
    shopSlug: offer.shop_slug,
    shopUrl: offer.shop_url,
    imageUrl: offer.image_url,
    brandName: offer.product_brand_name,
    price: offer.price,
    leafletUrl: offer.leaflet_url,
    pageNumber: offer.page_number,
    validFrom: offer.valid_from,
    validUntil: offer.valid_until,
  }));

const coverageSchema = z
  .object({
    shop_name: z.string(),
    shop_slug: z.string(),
    shop_url: z.string(),
    matched_query_count: z.number().int(),
    matched_queries: z.array(z.string()),
    offers: z.array(offerSchema),
  })
  .transform((coverage): ShopCoverage => ({
    shopName: coverage.shop_name,
    shopSlug: coverage.shop_slug,
    shopUrl: coverage.shop_url,
    matchedQueryCount: coverage.matched_query_count,
    matchedQueries: coverage.matched_queries,
    offers: coverage.offers,
  }));

export async function fetchShops(): Promise<PromotionShop[]> {
  const response = await http.get('/promotions/shops/');
  return shopSchema.array().parse(response.data);
}

export async function fetchFavouriteShopSlugs(): Promise<string[]> {
  const response = await http.get('/promotions/favourite-shops/');
  const favourites = favouriteShopSchema.array().parse(response.data);
  return favourites.map((shop) => shop.slug);
}

export async function saveFavouriteShopSlugs(slugs: string[]): Promise<string[]> {
  const response = await http.put('/promotions/favourite-shops/', { shops: slugs });
  const favourites = favouriteShopSchema.array().parse(response.data);
  return favourites.map((shop) => shop.slug);
}

export async function searchOffers(query: string, shopSlugs: string[]): Promise<PromotionOffer[]> {
  const params = shopSlugs.length === 0 ? { query } : { query, shop: shopSlugs };
  const response = await http.get('/promotions/search/', {
    params,
    paramsSerializer: { indexes: null },
  });
  return offerSchema.array().parse(response.data);
}

export async function compareShopCoverage(
  queries: string[],
  shopSlugs: string[],
): Promise<ShopCoverage[]> {
  const payload = shopSlugs.length === 0 ? { queries } : { queries, shops: shopSlugs };
  const response = await http.post('/promotions/store-coverage/', payload);
  return coverageSchema.array().parse(response.data);
}
