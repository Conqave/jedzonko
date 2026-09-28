import { beforeEach, describe, expect, it, vi } from 'vitest';
import { createRecipe, fetchExternalShortfall, fetchSuggestions } from './api';
import { createEmptyDraft } from './model';

const { get, post } = vi.hoisted(() => ({ get: vi.fn(), post: vi.fn() }));

vi.mock('@/shared/http', () => ({ http: { get, post } }));

const SHORTFALL_DTO = {
  missing_items: [
    { name: 'mleko', amount: '200.000', unit_code: 'ml' },
    { name: 'sól', amount: null, unit_code: null },
  ],
  required_item_count: 3,
  available_item_count: 1,
  unmeasured_ingredients: [],
  is_ready: false,
};

beforeEach(() => {
  get.mockReset();
  post.mockReset();
});

describe('recipes api', () => {
  it('reads suggestions with their nested shortfall', async () => {
    get.mockResolvedValue({
      data: [{ recipe_id: 1, recipe_name: 'Omlet', shortfall: SHORTFALL_DTO }],
    });

    const [suggestion] = await fetchSuggestions(7);

    expect(suggestion?.shortfall.missingItems[1]).toEqual({
      name: 'sól',
      amount: null,
      unitCode: null,
    });
  });

  it('asks for the shortfall of an external recipe in a household', async () => {
    get.mockResolvedValue({ data: SHORTFALL_DTO });

    await fetchExternalShortfall('omlet', 7);

    expect(get).toHaveBeenCalledWith('/recipes/external/omlet/missing-items/', {
      params: { household_id: 7 },
    });
  });

  it('numbers the steps of a new recipe', async () => {
    const draft = { ...createEmptyDraft(), name: 'Omlet', steps: ['Roztrzep.', 'Usmaż.'] };
    post.mockRejectedValue(new Error('stop'));

    await expect(createRecipe(draft)).rejects.toThrow('stop');

    const [, payload] = post.mock.calls[0] as [string, { steps: unknown }];
    expect(payload.steps).toEqual([
      { position: 1, text: 'Roztrzep.' },
      { position: 2, text: 'Usmaż.' },
    ]);
  });
});
