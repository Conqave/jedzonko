export const RECIPE_DIFFICULTIES = ['easy', 'medium', 'hard'] as const;

export type RecipeDifficulty = (typeof RECIPE_DIFFICULTIES)[number];

export const DIFFICULTY_LABELS: Readonly<Record<RecipeDifficulty, string>> = {
  easy: 'Łatwy',
  medium: 'Średni',
  hard: 'Trudny',
};

export interface RecipeSummary {
  id: number;
  name: string;
  description: string;
  servings: number;
  preparationTimeMinutes: number;
  cookingTimeMinutes: number;
  difficulty: RecipeDifficulty;
  categoryName: string | null;
  tags: string[];
  imageUrl: string | null;
  authorUsername: string;
}

export interface RecipeStep {
  position: number;
  text: string;
}

export interface RecipeIngredientLine {
  name: string;
  ingredientId: number | null;
  quantity: string;
  unitCode: string;
}

export interface RecipeDetail extends RecipeSummary {
  steps: RecipeStep[];
  ingredients: RecipeIngredientLine[];
}

export interface MissingRecipeItem {
  name: string;
  amount: string | null;
  unitCode: string | null;
}

export interface RecipeShortfall {
  missingItems: MissingRecipeItem[];
  requiredItemCount: number;
  availableItemCount: number;
  unmeasuredIngredients: string[];
  isReady: boolean;
}

export interface RecipeSuggestion {
  recipeId: number;
  recipeName: string;
  shortfall: RecipeShortfall;
}

export interface RecipeDraftIngredient {
  name: string;
  quantity: string;
  unitCode: string;
}

export interface RecipeDraft {
  name: string;
  description: string;
  servings: number;
  preparationTimeMinutes: number;
  cookingTimeMinutes: number;
  difficulty: RecipeDifficulty;
  tagNames: string[];
  steps: string[];
  ingredients: RecipeDraftIngredient[];
}

export interface ExternalRecipeSummary {
  sourceName: string;
  sourceUrl: string;
  reference: string;
  name: string;
  description: string;
  imageUrl: string | null;
  yieldLabel: string;
  totalTimeMinutes: number | null;
  tags: string[];
}

export interface ExternalRecipeMatch extends ExternalRecipeSummary {
  matchedProductNames: string[];
}

export interface ExternalRecipePage {
  recipes: ExternalRecipeMatch[];
  page: number;
  totalPages: number;
  totalCount: number;
}

export interface ExternalRecipeSuggestions {
  page: ExternalRecipePage;
  ingredientNames: string[];
  inventoryItemCount: number;
}

export interface ExternalRecipeIngredient {
  sourceText: string;
  name: string;
  quantity: string | null;
  unitCode: string | null;
}

export interface ExternalRecipe extends ExternalRecipeSummary {
  preparationTimeMinutes: number | null;
  cookingTimeMinutes: number | null;
  steps: string[];
  ingredients: ExternalRecipeIngredient[];
}

export function createEmptyDraft(): RecipeDraft {
  return {
    name: '',
    description: '',
    servings: 4,
    preparationTimeMinutes: 0,
    cookingTimeMinutes: 0,
    difficulty: 'easy',
    tagNames: [],
    steps: [''],
    ingredients: [{ name: '', quantity: '', unitCode: '' }],
  };
}

export function toDraft(recipe: RecipeDetail): RecipeDraft {
  const orderedSteps = [...recipe.steps].sort((left, right) => left.position - right.position);
  return {
    name: recipe.name,
    description: recipe.description,
    servings: recipe.servings,
    preparationTimeMinutes: recipe.preparationTimeMinutes,
    cookingTimeMinutes: recipe.cookingTimeMinutes,
    difficulty: recipe.difficulty,
    tagNames: [...recipe.tags],
    steps: orderedSteps.map((step) => step.text),
    ingredients: recipe.ingredients.map((line) => ({
      name: line.name,
      quantity: line.quantity,
      unitCode: line.unitCode,
    })),
  };
}

export function moveItem<T>(items: T[], index: number, offset: number): T[] {
  const target = index + offset;
  const moved = items[index];
  const displaced = items[target];
  if (moved === undefined || displaced === undefined) {
    return items;
  }
  const reordered = [...items];
  reordered[index] = displaced;
  reordered[target] = moved;
  return reordered;
}

export interface CookableSuggestion {
  suggestion: RecipeSuggestion;
  servings: number;
}

export function attachServings(
  suggestions: RecipeSuggestion[],
  recipes: RecipeSummary[],
): CookableSuggestion[] {
  const servingsById = new Map(recipes.map((recipe) => [recipe.id, recipe.servings]));
  const cookable: CookableSuggestion[] = [];
  for (const suggestion of suggestions) {
    const servings = servingsById.get(suggestion.recipeId);
    if (servings !== undefined) {
      cookable.push({ suggestion, servings });
    }
  }
  return cookable;
}
