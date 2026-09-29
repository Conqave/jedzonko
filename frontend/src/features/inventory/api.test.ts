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
  category_id: null,
  category_name: null,
  photo_url: null,
  below_minimum: false,
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
    });
  });

  it('sends a new item in the API shape', async () => {
    post.mockResolvedValue({ data: ITEM_DTO });

    await addInventoryItem({
      householdId: 1,
      productId: 7,
      quantity: '1.5',
      unitCode: 'l',
      minimumQuantity: null,
      categoryId: 3,
    });

    expect(post).toHaveBeenCalledWith('/inventory/', {
      household_id: 1,
      product_id: 7,
      quantity: '1.5',
      unit_code: 'l',
      minimum_quantity: null,
      category_id: 3,
    });
  });

  it('sends only the changed fields', async () => {
    patch.mockResolvedValue({ data: ITEM_DTO });

    await updateInventoryItem(5, { quantity: '2.000' });

    expect(patch).toHaveBeenCalledWith('/inventory/5/', {
      product_name: undefined,
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
