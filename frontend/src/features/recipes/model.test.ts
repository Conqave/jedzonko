import { describe, expect, it } from 'vitest';
import {
  arrangeRecipes,
  arrangeSuggestions,
  attachRecipes,
  describeNutrition,
  describeRecipeCalories,
  moveItem,
  toDraft,
  type RecipeDetail,
  type RecipeListing,
  type RecipeView,
} from './model';

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

const PANCAKE_LISTING: RecipeListing = {
  ...PANCAKES,
  nutrition: {
    totalKcal: '1310.4',
    kcalPerServing: '327.6',
    hasEstimates: true,
    uncountedIngredients: [{ name: 'sól', reason: 'no_amount' }],
  },
  ingredientNames: ['Mąka', 'mąka pszenna'],
};

describe('recipe model', () => {
  it('turns a recipe into a draft with steps in order', () => {
    const draft = toDraft(PANCAKES);

    expect(draft.steps).toEqual(['Wymieszaj.', 'Usmaż.']);
    expect(draft.categoryId).toBe(2);
    expect(draft.ingredients).toEqual([{ name: 'Mąka', quantity: '300', unitCode: 'g' }]);
  });

  it('moves a step without touching the original list', () => {
    const steps = ['a', 'b', 'c'];

    expect(moveItem(steps, 2, -1)).toEqual(['a', 'c', 'b']);
    expect(steps).toEqual(['a', 'b', 'c']);
  });

  it('keeps a list as it is when a move leaves it', () => {
    expect(moveItem(['a', 'b'], 0, -1)).toEqual(['a', 'b']);
  });

  it('joins suggestions with their recipe and drops the orphans', () => {
    const suggestion = { recipeId: 1, recipeName: 'Naleśniki', shortfall: SHORTFALL };
    const orphan = { recipeId: 9, recipeName: 'Zniknął', shortfall: SHORTFALL };

    expect(attachRecipes([suggestion, orphan], [PANCAKE_LISTING])).toEqual([
      { suggestion, recipe: PANCAKE_LISTING },
    ]);
  });

  it('describes calories in total and per serving', () => {
    const nutrition = {
      totalKcal: '1310.4',
      kcalPerServing: '327.6',
      hasEstimates: false,
      uncountedIngredients: [],
    };

    expect(describeNutrition(nutrition)).toBe('ok. 1310 kcal · 328 kcal/porcję');
  });

  it('gives only the total when servings are unknown', () => {
    const nutrition = {
      totalKcal: '899.6',
      kcalPerServing: null,
      hasEstimates: true,
      uncountedIngredients: [],
    };

    expect(describeNutrition(nutrition)).toBe('ok. 900 kcal');
  });

  it('admits unknown calories when nothing could be counted', () => {
    const uncounted = [{ name: 'sól', reason: 'no_amount' as const }];
    const nutrition = {
      totalKcal: '0.0',
      kcalPerServing: null,
      hasEstimates: false,
      uncountedIngredients: uncounted,
    };

    expect(describeNutrition(nutrition)).toBe('Kalorie nieznane');
  });
});

const SOUP: RecipeListing = {
  ...PANCAKE_LISTING,
  id: 2,
  name: 'Żurek',
  preparationTimeMinutes: 20,
  cookingTimeMinutes: 40,
  category: { id: 3, name: 'zupy' },
  tags: ['wielkanoc'],
  nutrition: {
    totalKcal: '0.0',
    kcalPerServing: '0.0',
    hasEstimates: false,
    uncountedIngredients: [{ name: 'zakwas', reason: 'no_calories' }],
  },
  ingredientNames: ['zakwas', 'kiełbasa biała'],
};

const SALAD: RecipeListing = {
  ...PANCAKE_LISTING,
  id: 3,
  name: 'Sałatka',
  preparationTimeMinutes: 15,
  cookingTimeMinutes: 0,
  category: null,
  tags: ['szybkie'],
  nutrition: {
    totalKcal: '240.0',
    kcalPerServing: '120.0',
    hasEstimates: false,
    uncountedIngredients: [],
  },
  ingredientNames: ['ogórek'],
};

const BY_NAME: RecipeView = { search: '', sort: 'name', isReversed: false };

function recipeNames(recipes: RecipeListing[]): string[] {
  return recipes.map((recipe) => recipe.name);
}

describe('recipe list view', () => {
  const recipes = [SOUP, PANCAKE_LISTING, SALAD];

  it('sorts by name in Polish order', () => {
    expect(recipeNames(arrangeRecipes(recipes, BY_NAME))).toEqual([
      'Naleśniki',
      'Sałatka',
      'Żurek',
    ]);
  });

  it('sorts by total time, shortest first unless reversed', () => {
    const byTime: RecipeView = { ...BY_NAME, sort: 'time' };
    const reversed: RecipeView = { ...byTime, isReversed: true };

    expect(recipeNames(arrangeRecipes(recipes, byTime))).toEqual(['Sałatka', 'Naleśniki', 'Żurek']);
    expect(recipeNames(arrangeRecipes(recipes, reversed))).toEqual([
      'Żurek',
      'Naleśniki',
      'Sałatka',
    ]);
  });

  it('searches the name, tags and category without diacritics', () => {
    const search = (text: string) =>
      recipeNames(arrangeRecipes(recipes, { ...BY_NAME, search: text }));

    expect(search('zurek')).toEqual(['Żurek']);
    expect(search('WIELKANOC')).toEqual(['Żurek']);
    expect(search('obiady')).toEqual(['Naleśniki']);
    expect(search('salat szyb')).toEqual(['Sałatka']);
    expect(search('pierogi')).toEqual([]);
  });

  it('sorts by calories per serving with unknown calories last either way', () => {
    const byCalories: RecipeView = { ...BY_NAME, sort: 'calories' };
    const reversed: RecipeView = { ...byCalories, isReversed: true };

    expect(recipeNames(arrangeRecipes(recipes, byCalories))).toEqual([
      'Sałatka',
      'Naleśniki',
      'Żurek',
    ]);
    expect(recipeNames(arrangeRecipes(recipes, reversed))).toEqual([
      'Naleśniki',
      'Sałatka',
      'Żurek',
    ]);
  });

  it('searches the ingredients and their tags', () => {
    const search = (text: string) =>
      recipeNames(arrangeRecipes(recipes, { ...BY_NAME, search: text }));

    expect(search('kielbasa')).toEqual(['Żurek']);
    expect(search('maka pszenna')).toEqual(['Naleśniki']);
  });

  it('filters suggestions by readiness and search, sorted like recipes', () => {
    const missing = { ...SHORTFALL, isReady: false };
    const cookable = [
      { suggestion: { recipeId: 2, recipeName: 'Żurek', shortfall: SHORTFALL }, recipe: SOUP },
      {
        suggestion: { recipeId: 1, recipeName: 'Naleśniki', shortfall: missing },
        recipe: PANCAKE_LISTING,
      },
      { suggestion: { recipeId: 3, recipeName: 'Sałatka', shortfall: SHORTFALL }, recipe: SALAD },
    ];
    const names = (isReadyOnly: boolean, view: RecipeView) =>
      arrangeSuggestions(cookable, view, isReadyOnly).map((entry) => entry.recipe.name);

    expect(names(false, BY_NAME)).toEqual(['Naleśniki', 'Sałatka', 'Żurek']);
    expect(names(true, BY_NAME)).toEqual(['Sałatka', 'Żurek']);
    expect(names(true, { ...BY_NAME, search: 'zupy' })).toEqual(['Żurek']);
  });
});

describe('recipe calories in the list', () => {
  it('shows calories per serving marked as an estimate with what was left out', () => {
    expect(describeRecipeCalories(PANCAKE_LISTING.nutrition)).toEqual({
      text: '328 kcal/porcję',
      isKnown: true,
      isEstimate: true,
      tooltip: 'Szacunek z wagi sztuki, gęstości lub opakowania. Nie wliczono: sól (brak ilości).',
      caption: null,
    });
  });

  it('shows the total when servings are unknown', () => {
    const nutrition = { ...SALAD.nutrition, kcalPerServing: null };

    expect(describeRecipeCalories(nutrition).text).toBe('240 kcal');
  });

  it('shows a hyphen and the reason when nothing could be counted', () => {
    expect(describeRecipeCalories(SOUP.nutrition)).toEqual({
      text: '-',
      isKnown: false,
      isEstimate: false,
      tooltip: 'Nie wliczono: zakwas (tag bez kalorii).',
      caption: null,
    });
  });
});
