import { beforeEach, describe, expect, it, vi } from 'vitest';
import { addRecipeItems, addShoppingItem, fetchShoppingItems } from './api';

const { get, post } = vi.hoisted(() => ({ get: vi.fn(), post: vi.fn() }));

vi.mock('@/shared/http', () => ({ http: { get, post } }));

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
});
