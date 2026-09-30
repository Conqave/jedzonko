import { beforeEach, describe, expect, it, vi } from 'vitest';
import {
  addInventoryItem,
  fetchInventory,
  setInventoryItemMinimum,
  updateInventoryItem,
} from './api';

const { get, post, patch, put } = vi.hoisted(() => ({
  get: vi.fn(),
  post: vi.fn(),
  patch: vi.fn(),
  put: vi.fn(),
}));

vi.mock('@/shared/http', () => ({ http: { get, post, patch, put } }));

const ITEM_DTO = {
  id: 5,
  product_id: 7,
  product_name: 'Mleko',
  quantity: '1.500',
  unit_code: 'l',
  minimum_quantity: '1.000',
  photo_url: null,
  below_minimum: false,
  calories: { kcal: '960.0', kcal_per_100g: '64.0', is_estimate: true, uncounted_reason: null },
};

beforeEach(() => {
  get.mockReset();
  post.mockReset();
  patch.mockReset();
});

describe('inventory api', () => {
  it('maps items to the model', async () => {
    get.mockResolvedValue({ data: [ITEM_DTO] });

    const [item] = await fetchInventory(1);

    expect(get).toHaveBeenCalledWith('/inventory/', { params: { household_id: 1 } });
    expect(item).toMatchObject({
      productName: 'Mleko',
      minimumQuantity: '1.000',
      isBelowMinimum: false,
      calories: { kind: 'counted', kcal: '960.0', kcalPer100g: '64.0', isEstimate: true },
    });
  });

  it('maps calories that could not be counted to their reason', async () => {
    const calories = {
      kcal: null,
      kcal_per_100g: null,
      is_estimate: false,
      uncounted_reason: 'several_tags',
    };
    get.mockResolvedValue({ data: [{ ...ITEM_DTO, calories }] });

    const [item] = await fetchInventory(1);

    expect(item?.calories).toEqual({
      kind: 'uncounted',
      reason: 'several_tags',
      kcalPer100g: null,
    });
  });

  it('rejects calories that are both counted and explained', async () => {
    const calories = {
      kcal: '1.0',
      kcal_per_100g: null,
      is_estimate: false,
      uncounted_reason: 'no_tag',
    };
    get.mockResolvedValue({ data: [{ ...ITEM_DTO, calories }] });

    await expect(fetchInventory(1)).rejects.toThrow();
  });

  it('sends a new item in the API shape', async () => {
    post.mockResolvedValue({ data: ITEM_DTO });

    await addInventoryItem({
      householdId: 1,
      productId: 7,
      quantity: '1.5',
      unitCode: 'l',
      minimumQuantity: null,
    });

    expect(post).toHaveBeenCalledWith('/inventory/', {
      household_id: 1,
      product_id: 7,
      quantity: '1.5',
      unit_code: 'l',
      minimum_quantity: null,
    });
  });

  it('sends only the changed fields', async () => {
    patch.mockResolvedValue({ data: ITEM_DTO });

    await updateInventoryItem(5, { quantity: '2.000' });

    expect(patch).toHaveBeenCalledWith('/inventory/5/', {
      quantity: '2.000',
      unit_code: undefined,
    });
  });

  it('rejects an item that breaks the contract', async () => {
    get.mockResolvedValue({ data: [{ ...ITEM_DTO, quantity: 1.5 }] });

    await expect(fetchInventory(1)).rejects.toThrow();
  });

  it('clears the minimum quantity with an explicit null', async () => {
    put.mockResolvedValue({ data: { ...ITEM_DTO, minimum_quantity: null, below_minimum: false } });

    const item = await setInventoryItemMinimum(5, null);

    expect(put).toHaveBeenCalledWith('/inventory/5/minimum/', { minimum_quantity: null });
    expect(item.minimumQuantity).toBeNull();
  });
});
