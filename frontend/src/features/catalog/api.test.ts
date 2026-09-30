import { beforeEach, describe, expect, it, vi } from 'vitest';
import {
  createProduct,
  fetchProductDecisions,
  searchProducts,
  setTagCalories,
  setTagDensity,
  setTagPieceWeight,
} from './api';

const { get, post, put } = vi.hoisted(() => ({ get: vi.fn(), post: vi.fn(), put: vi.fn() }));

vi.mock('@/shared/http', () => ({ http: { get, post, put } }));

const PRODUCT_DTO = {
  id: 7,
  household_id: 1,
  name: 'Mleko 2%',
  default_unit_code: 'l',
  is_food: true,
  package: { quantity: '1.000', unit_code: 'l' },
};

beforeEach(() => {
  get.mockReset();
  post.mockReset();
  put.mockReset();
});

describe('catalog api', () => {
  it('maps a listing with all its tags', async () => {
    const listing = {
      product: PRODUCT_DTO,
      tags: [
        { ingredient_id: 3, name: 'mleko' },
        { ingredient_id: 8, name: 'mleko zsiadłe' },
      ],
      open_proposal_count: 1,
    };
    get.mockResolvedValue({ data: [listing] });

    const [found] = await searchProducts(1, 'mle');

    expect(get).toHaveBeenCalledWith('/products/', { params: { household_id: 1, search: 'mle' } });
    expect(found?.tags).toEqual([
      { id: 3, name: 'mleko' },
      { id: 8, name: 'mleko zsiadłe' },
    ]);
    expect(found?.product.package).toEqual({ quantity: '1.000', unitCode: 'l' });
  });

  it('asks for every product when the search is empty', async () => {
    get.mockResolvedValue({ data: [] });

    await searchProducts(1, '');

    expect(get).toHaveBeenCalledWith('/products/', { params: { household_id: 1 } });
  });

  it('sends a new product in the API shape', async () => {
    post.mockResolvedValue({ data: PRODUCT_DTO });

    await createProduct({
      householdId: 1,
      name: 'Mleko 2%',
      defaultUnitCode: 'l',
      isFood: true,
      package: { quantity: '1', unitCode: 'l' },
    });

    expect(post).toHaveBeenCalledWith('/products/', {
      household_id: 1,
      name: 'Mleko 2%',
      default_unit_code: 'l',
      is_food: true,
      package: { quantity: '1', unit_code: 'l' },
    });
  });

  it('reads the calories and conversions of each decided tag', async () => {
    const decision = {
      status: 'confirmed',
      provenance: 'manual',
      model_name: null,
      proposed_at: null,
      decided_at: '2026-09-30T08:00:00+02:00',
    };
    get.mockResolvedValue({
      data: [
        {
          ...decision,
          ingredient: {
            id: 3,
            name: 'jabłko',
            calories: {
              kcal_per_100g: '52.0',
              provenance: 'reference',
              reference_url: 'https://example.org/apple',
            },
            piece_weight: {
              grams_per_piece: '180.0',
              provenance: 'manual',
              reference_url: null,
            },
            density: null,
          },
        },
        {
          ...decision,
          ingredient: {
            id: 4,
            name: 'woda',
            calories: null,
            piece_weight: null,
            density: { grams_per_ml: '1.000', provenance: 'manual', reference_url: null },
          },
        },
      ],
    });

    const [apple, water] = await fetchProductDecisions(7);

    expect(apple?.ingredient).toEqual({ id: 3, name: 'jabłko' });
    expect(apple?.calories).toEqual({
      kcalPer100g: '52.0',
      provenance: 'reference',
      referenceUrl: 'https://example.org/apple',
    });
    expect(apple?.pieceWeight).toEqual({
      gramsPerPiece: '180.0',
      provenance: 'manual',
      referenceUrl: null,
    });
    expect(apple?.density).toBeNull();
    expect(water?.calories).toBeNull();
    expect(water?.pieceWeight).toBeNull();
    expect(water?.density).toEqual({
      gramsPerMl: '1.000',
      provenance: 'manual',
      referenceUrl: null,
    });
  });

  it('sets or clears the calories of a tag', async () => {
    put.mockResolvedValue({
      data: { id: 3, name: 'jabłko', calories: null, piece_weight: null, density: null },
    });

    const calories = await setTagCalories(3, null);

    expect(put).toHaveBeenCalledWith('/ingredients/3/calories/', { kcal_per_100g: null });
    expect(calories).toBeNull();
  });

  it('sets the piece weight and the density of a tag', async () => {
    const tag = {
      id: 3,
      name: 'jajka',
      calories: null,
      piece_weight: { grams_per_piece: '55.0', provenance: 'manual', reference_url: null },
      density: { grams_per_ml: '1.030', provenance: 'manual', reference_url: null },
    };
    put.mockResolvedValue({ data: tag });

    const pieceWeight = await setTagPieceWeight(3, '55');
    const density = await setTagDensity(3, '1.03');

    expect(put).toHaveBeenCalledWith('/ingredients/3/piece-weight/', { grams_per_piece: '55' });
    expect(put).toHaveBeenCalledWith('/ingredients/3/density/', { grams_per_ml: '1.03' });
    expect(pieceWeight?.gramsPerPiece).toBe('55.0');
    expect(density?.gramsPerMl).toBe('1.030');
  });

  it('rejects a tag without its conversions', async () => {
    put.mockResolvedValue({ data: { id: 3, name: 'jajka', calories: null } });

    await expect(setTagPieceWeight(3, null)).rejects.toThrow();
  });
});
