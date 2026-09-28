import { beforeEach, describe, expect, it, vi } from 'vitest';
import { createProduct, searchProducts } from './api';

const { get, post } = vi.hoisted(() => ({ get: vi.fn(), post: vi.fn() }));

vi.mock('@/shared/http', () => ({ http: { get, post } }));

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
});

describe('catalog api', () => {
  it('maps a listing with its confirmed ingredient', async () => {
    const listing = {
      product: PRODUCT_DTO,
      ingredient_id: 3,
      ingredient_name: 'mleko',
      open_proposal_count: 1,
    };
    get.mockResolvedValue({ data: [listing] });

    const [found] = await searchProducts(1, 'mle');

    expect(get).toHaveBeenCalledWith('/products/', { params: { household_id: 1, search: 'mle' } });
    expect(found?.ingredient).toEqual({ id: 3, name: 'mleko' });
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
});
