import { beforeEach, describe, expect, it, vi } from 'vitest';
import { compareShopCoverage, saveFavouriteShopSlugs, searchOffers } from './api';

const { get, post, put } = vi.hoisted(() => ({ get: vi.fn(), post: vi.fn(), put: vi.fn() }));

vi.mock('@/shared/http', () => ({ http: { get, post, put } }));

const OFFER_DTO = {
  provider_offer_id: '1',
  name: 'Mleko',
  shop_name: 'Lidl',
  shop_slug: 'lidl',
  shop_url: 'https://lidl.test',
  image_url: 'https://lidl.test/mleko.png',
  product_brand_name: null,
  price: '3.99',
  leaflet_provider_id: 'abc',
  leaflet_url: 'https://lidl.test/gazetka',
  page_number: 2,
  valid_from: '2026-09-28',
  valid_until: '2026-10-04',
};

beforeEach(() => {
  get.mockReset();
  post.mockReset();
  put.mockReset();
});

describe('promotions api', () => {
  it('maps offers to the model', async () => {
    get.mockResolvedValue({ data: [OFFER_DTO] });

    const [offer] = await searchOffers('mleko', []);

    expect(offer?.shopSlug).toBe('lidl');
    expect(offer?.leafletUrl).toBe('https://lidl.test/gazetka');
  });

  it('narrows a search to the chosen shops', async () => {
    get.mockResolvedValue({ data: [] });

    await searchOffers('mleko', ['lidl']);

    expect(get).toHaveBeenCalledWith('/promotions/search/', {
      params: { query: 'mleko', shop: ['lidl'] },
      paramsSerializer: { indexes: null },
    });
  });

  it('maps store coverage with its offers', async () => {
    const coverage = {
      shop_name: 'Lidl',
      shop_slug: 'lidl',
      shop_url: 'https://lidl.test',
      matched_query_count: 1,
      matched_queries: ['mleko'],
      offers: [OFFER_DTO],
    };
    post.mockResolvedValue({ data: [coverage] });

    const [entry] = await compareShopCoverage(['mleko'], []);

    expect(post).toHaveBeenCalledWith('/promotions/store-coverage/', { queries: ['mleko'] });
    expect(entry?.matchedQueries).toEqual(['mleko']);
    expect(entry?.offers[0]?.name).toBe('Mleko');
  });

  it('returns the saved favourite slugs', async () => {
    put.mockResolvedValue({ data: [{ name: 'Lidl', slug: 'lidl' }] });

    await expect(saveFavouriteShopSlugs(['lidl'])).resolves.toEqual(['lidl']);
  });

  it('rejects an offer that breaks the contract', async () => {
    get.mockResolvedValue({ data: [{ ...OFFER_DTO, page_number: 'two' }] });

    await expect(searchOffers('mleko', [])).rejects.toThrow();
  });
});
