import { describe, expect, it } from 'vitest';
import { attachServings, moveItem, toDraft, type RecipeDetail } from './model';

const SHORTFALL = {
  missingItems: [],
  requiredItemCount: 1,
  availableItemCount: 1,
  unmeasuredIngredients: [],
  isReady: true,
};

const PANCAKES: RecipeDetail = {
  id: 1,
  name: 'Naleśniki',
  description: '',
  servings: 4,
  preparationTimeMinutes: 10,
  cookingTimeMinutes: 20,
  difficulty: 'easy',
  category: { id: 2, name: 'obiady' },
  tags: ['obiad'],
  imageUrl: null,
  authorUsername: 'ala',
  steps: [
    { position: 2, text: 'Usmaż.' },
    { position: 1, text: 'Wymieszaj.' },
  ],
  ingredients: [{ name: 'Mąka', ingredientId: 3, quantity: '300.000', unitCode: 'g' }],
};

describe('recipe model', () => {
  it('turns a recipe into a draft with steps in order', () => {
    const draft = toDraft(PANCAKES);

    expect(draft.steps).toEqual(['Wymieszaj.', 'Usmaż.']);
    expect(draft.categoryId).toBe(2);
    expect(draft.ingredients).toEqual([{ name: 'Mąka', quantity: '300.000', unitCode: 'g' }]);
  });

  it('moves a step without touching the original list', () => {
    const steps = ['a', 'b', 'c'];

    expect(moveItem(steps, 2, -1)).toEqual(['a', 'c', 'b']);
    expect(steps).toEqual(['a', 'b', 'c']);
  });

  it('keeps a list as it is when a move leaves it', () => {
    expect(moveItem(['a', 'b'], 0, -1)).toEqual(['a', 'b']);
  });

  it('gives suggestions the servings of their recipe', () => {
    const suggestion = { recipeId: 1, recipeName: 'Naleśniki', shortfall: SHORTFALL };
    const orphan = { recipeId: 9, recipeName: 'Zniknął', shortfall: SHORTFALL };

    expect(attachServings([suggestion, orphan], [PANCAKES])).toEqual([{ suggestion, servings: 4 }]);
  });
});
