import { beforeEach, describe, expect, it, vi } from 'vitest';
import {
  addRecipeItems,
  addShoppingItem,
  buyShoppingItems,
  fetchShoppingItems,
  interpretShoppingItem,
  tagShoppingItem,
} from './api';

const { get, post, put } = vi.hoisted(() => ({ get: vi.fn(), post: vi.fn(), put: vi.fn() }));

vi.mock('@/shared/http', () => ({ http: { get, post, put } }));

const ITEM_DTO = {
  id: 5,
  list_id: 2,
  product_id: null,
  ingredient_id: 9,
  free_text: null,
  name: 'jajka',
  quantity: '3.000',
  unit_code: 'szt',
  status: 'pending',
  purchased_at: null,
};

beforeEach(() => {
  get.mockReset();
  post.mockReset();
  put.mockReset();
});

describe('shopping api', () => {
  it('maps an item to its subject', async () => {
    get.mockResolvedValue({ data: [ITEM_DTO] });

    const [item] = await fetchShoppingItems(2);

    expect(item?.subject).toEqual({ kind: 'ingredient', ingredientId: 9 });
    expect(item?.unitCode).toBe('szt');
  });

  it('rejects an item about two things', async () => {
    get.mockResolvedValue({ data: [{ ...ITEM_DTO, free_text: 'jajka' }] });

    await expect(fetchShoppingItems(2)).rejects.toThrow();
  });

  it('sends exactly one subject field', async () => {
    post.mockResolvedValue({ data: { ...ITEM_DTO, ingredient_id: null, free_text: 'sól' } });

    await addShoppingItem(2, {
      subject: { kind: 'text', text: 'sól' },
      quantity: '1',
      unitCode: null,
    });

    expect(post).toHaveBeenCalledWith('/shopping/lists/2/items/', {
      product_id: null,
      ingredient_id: null,
      free_text: 'sól',
      quantity: '1',
      unit_code: null,
    });
  });

  it('posts an external recipe to its endpoint', async () => {
    post.mockResolvedValue({ data: [] });

    await addRecipeItems(2, { kind: 'external', reference: 'omlet' });

    expect(post).toHaveBeenCalledWith('/shopping/lists/2/external-recipe-items/', {
      reference: 'omlet',
    });
  });

  it('posts an own recipe with its servings', async () => {
    post.mockResolvedValue({ data: [] });

    await addRecipeItems(2, { kind: 'recipe', recipeId: 4, servings: 3 });

    expect(post).toHaveBeenCalledWith('/shopping/lists/2/recipe-items/', {
      recipe_id: 4,
      servings: 3,
    });
  });

  it('puts a tag with its amount on an item', async () => {
    put.mockResolvedValue({ data: ITEM_DTO });

    const item = await tagShoppingItem(5, { ingredientId: 9, quantity: '6', unitCode: 'szt' });

    expect(put).toHaveBeenCalledWith('/shopping/items/5/ingredient/', {
      ingredient_id: 9,
      quantity: '6',
      unit_code: 'szt',
    });
    expect(item.subject).toEqual({ kind: 'ingredient', ingredientId: 9 });
  });

  it('maps the model proposal to an ingredient', async () => {
    const proposal = {
      ingredient_id: 9,
      ingredient_name: 'Jajka',
      quantity: '6.000',
      unit_code: 'szt',
    };
    post.mockResolvedValue({ data: proposal });

    const interpretation = await interpretShoppingItem(5);

    expect(post).toHaveBeenCalledWith('/shopping/items/5/interpretation/');
    expect(interpretation).toEqual({
      ingredient: { id: 9, name: 'Jajka' },
      quantity: '6.000',
      unitCode: 'szt',
    });
  });

  it('maps an unrecognised line to an empty proposal', async () => {
    const proposal = {
      ingredient_id: null,
      ingredient_name: null,
      quantity: null,
      unit_code: null,
    };
    post.mockResolvedValue({ data: proposal });

    const interpretation = await interpretShoppingItem(5);

    expect(interpretation).toEqual({ ingredient: null, quantity: null, unitCode: null });
  });

  it('posts every bought item with its chosen product', async () => {
    post.mockResolvedValue({ data: null });

    await buyShoppingItems(2, [
      { itemId: 5, productId: 4 },
      { itemId: 6, productId: null },
    ]);

    expect(post).toHaveBeenCalledWith('/shopping/lists/2/purchase/', {
      items: [
        { item_id: 5, product_id: 4 },
        { item_id: 6, product_id: null },
      ],
    });
  });
});
