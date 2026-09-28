export interface PromotionShop {
  name: string;
  slug: string;
  url: string;
}

export interface PromotionOffer {
  providerOfferId: string | null;
  name: string;
  shopName: string;
  shopSlug: string;
  shopUrl: string;
  imageUrl: string;
  brandName: string | null;
  price: string | null;
  leafletUrl: string;
  pageNumber: number;
  validFrom: string;
  validUntil: string;
}

export interface ShopCoverage {
  shopName: string;
  shopSlug: string;
  shopUrl: string;
  matchedQueryCount: number;
  matchedQueries: string[];
  offers: PromotionOffer[];
}

export interface OfferGroup {
  shopSlug: string;
  shopName: string;
  offers: PromotionOffer[];
}

export function groupOffersByShop(offers: PromotionOffer[]): OfferGroup[] {
  const groups = new Map<string, OfferGroup>();
  for (const offer of offers) {
    const existing = groups.get(offer.shopSlug);
    if (existing === undefined) {
      groups.set(offer.shopSlug, {
        shopSlug: offer.shopSlug,
        shopName: offer.shopName,
        offers: [offer],
      });
      continue;
    }
    existing.offers.push(offer);
  }
  return [...groups.values()];
}

export function findBestCoverage(coverage: ShopCoverage[]): ShopCoverage[] {
  const best = coverage[0];
  if (best === undefined || best.matchedQueryCount === 0) {
    return [];
  }
  return coverage.filter((entry) => entry.matchedQueryCount === best.matchedQueryCount);
}

export function findMissingQueries(entry: ShopCoverage, queries: string[]): string[] {
  return queries.filter((query) => !entry.matchedQueries.includes(query));
}

export function formatPrice(price: string | null): string {
  return price === null ? 'brak ceny' : `${price} zł`;
}
