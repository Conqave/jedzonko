import { describe, expect, it } from 'vitest';
import {
  findBestCoverage,
  findMissingQueries,
  formatPrice,
  groupOffersByShop,
  type PromotionOffer,
  type ShopCoverage,
} from './model';

function makeOffer(shopSlug: string, name: string): PromotionOffer {
  return {
    providerOfferId: null,
    name,
    shopName: shopSlug.toUpperCase(),
    shopSlug,
    shopUrl: `https://example.test/${shopSlug}`,
    imageUrl: '',
    brandName: null,
    price: '3.99',
    leafletUrl: '',
    pageNumber: 1,
    validFrom: '2026-09-28',
    validUntil: '2026-10-04',
  };
}

function makeCoverage(shopSlug: string, matchedQueries: string[]): ShopCoverage {
  return {
    shopName: shopSlug,
    shopSlug,
    shopUrl: '',
    matchedQueryCount: matchedQueries.length,
    matchedQueries,
    offers: [],
  };
}

describe('promotions model', () => {
  it('groups offers by shop in order of appearance', () => {
    const offers = [
      makeOffer('lidl', 'mleko'),
      makeOffer('biedronka', 'ser'),
      makeOffer('lidl', 'masło'),
    ];

    const groups = groupOffersByShop(offers);

    expect(groups.map((group) => [group.shopSlug, group.offers.length])).toEqual([
      ['lidl', 2],
      ['biedronka', 1],
    ]);
  });

  it('finds every shop tied for the best coverage', () => {
    const coverage = [
      makeCoverage('lidl', ['mleko', 'ser']),
      makeCoverage('biedronka', ['mleko', 'masło']),
      makeCoverage('aldi', ['mleko']),
    ];

    expect(findBestCoverage(coverage).map((entry) => entry.shopSlug)).toEqual([
      'lidl',
      'biedronka',
    ]);
  });

  it('finds no best shop when nothing matched', () => {
    expect(findBestCoverage([makeCoverage('lidl', [])])).toEqual([]);
  });

  it('lists the queries a shop does not cover', () => {
    const entry = makeCoverage('lidl', ['mleko']);

    expect(findMissingQueries(entry, ['mleko', 'ser'])).toEqual(['ser']);
  });

  it('shows a missing price in words', () => {
    expect(formatPrice(null)).toBe('brak ceny');
    expect(formatPrice('3.99')).toBe('3.99 zł');
  });
});
