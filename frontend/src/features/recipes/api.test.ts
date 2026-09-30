import { beforeEach, describe, expect, it, vi } from 'vitest';
import {
  createRecipe,
  fetchExternalRecipeNutrition,
  fetchExternalShortfall,
  fetchRecipeNutrition,
  fetchRecipes,
  fetchSuggestions,
} from './api';
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

  it('lists recipes with their calories and ingredient names', async () => {
    get.mockResolvedValue({
      data: [
        {
          id: 1,
          name: 'Omlet',
          description: '',
          servings: 2,
          preparation_time_minutes: 5,
          cooking_time_minutes: 5,
          difficulty: 'easy',
          category: null,
          tags: [],
          image_url: null,
          author_username: null,
          nutrition: {
            total_kcal: '286.0',
            kcal_per_serving: '143.0',
            has_estimates: false,
            uncounted_ingredients: [],
          },
          ingredient_names: ['jajko'],
        },
      ],
    });

    const [recipe] = await fetchRecipes();

    expect(recipe?.nutrition.kcalPerServing).toBe('143.0');
    expect(recipe?.ingredientNames).toEqual(['jajko']);
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

  it('reads the nutrition of a recipe with what was not counted', async () => {
    get.mockResolvedValue({
      data: {
        total_kcal: '1310.0',
        kcal_per_serving: '327.5',
        has_estimates: true,
        uncounted_ingredients: [{ name: 'mleko', reason: 'no_density' }],
      },
    });

    const nutrition = await fetchRecipeNutrition(4);

    expect(get).toHaveBeenCalledWith('/recipes/4/nutrition/');
    expect(nutrition).toEqual({
      totalKcal: '1310.0',
      kcalPerServing: '327.5',
      hasEstimates: true,
      uncountedIngredients: [{ name: 'mleko', reason: 'no_density' }],
    });
  });

  it('rejects an unknown reason for an uncounted line', async () => {
    get.mockResolvedValue({
      data: {
        total_kcal: '0.0',
        kcal_per_serving: null,
        has_estimates: false,
        uncounted_ingredients: [{ name: 'mleko', reason: 'not_by_mass' }],
      },
    });

    await expect(fetchExternalRecipeNutrition('omlet')).rejects.toThrow();
    expect(get).toHaveBeenCalledWith('/recipes/external/omlet/nutrition/');
  });
});
