import {
  ESTIMATE_TOOLTIP,
  UNCOUNTED_REASON_LABELS,
  UNKNOWN_KCAL_TEXT,
  roundKcal,
  type KcalDisplay,
  type UncountedReason,
} from '@/shared/calories';
import { formatQuantity } from '@/shared/formatQuantity';
import { sortByKeys, type SortKey } from '@/shared/listView';
import { matchesSearch } from '@/shared/textSearch';

export const RECIPE_DIFFICULTIES = ['easy', 'medium', 'hard'] as const;

export type RecipeDifficulty = (typeof RECIPE_DIFFICULTIES)[number];

export const DIFFICULTY_LABELS: Readonly<Record<RecipeDifficulty, string>> = {
  easy: 'Łatwy',
  medium: 'Średni',
  hard: 'Trudny',
};

export interface RecipeCategory {
  id: number;
  name: string;
}

export interface RecipeSummary {
  id: number;
  name: string;
  description: string;
  servings: number;
  preparationTimeMinutes: number;
  cookingTimeMinutes: number;
  difficulty: RecipeDifficulty;
  category: RecipeCategory | null;
  tags: string[];
  imageUrl: string | null;
  authorUsername: string | null;
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

export interface UncountedIngredient {
  name: string;
  reason: UncountedReason;
}

export interface RecipeNutrition {
  totalKcal: string;
  kcalPerServing: string | null;
  hasEstimates: boolean;
  uncountedIngredients: UncountedIngredient[];
}

export function isNutritionUnknown(nutrition: RecipeNutrition): boolean {
  return Number(nutrition.totalKcal) === 0 && nutrition.uncountedIngredients.length > 0;
}

export function describeNutrition(nutrition: RecipeNutrition): string {
  if (isNutritionUnknown(nutrition)) {
    return 'Kalorie nieznane';
  }
  const total = `ok. ${roundKcal(nutrition.totalKcal)} kcal`;
  if (nutrition.kcalPerServing === null) {
    return total;
  }
  return `${total} · ${roundKcal(nutrition.kcalPerServing)} kcal/porcję`;
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
  categoryId: number | null;
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
    categoryId: null,
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
    categoryId: recipe.category === null ? null : recipe.category.id,
    tagNames: [...recipe.tags],
    steps: orderedSteps.map((step) => step.text),
    ingredients: recipe.ingredients.map((line) => ({
      name: line.name,
      quantity: formatQuantity(line.quantity),
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

export interface RecipeListing extends RecipeSummary {
  nutrition: RecipeNutrition;
  ingredientNames: string[];
}

function findRecipeKcal(nutrition: RecipeNutrition): string | null {
  if (isNutritionUnknown(nutrition)) {
    return null;
  }
  return nutrition.kcalPerServing ?? nutrition.totalKcal;
}

function describeUncountedIngredients(nutrition: RecipeNutrition): string | null {
  if (nutrition.uncountedIngredients.length === 0) {
    return null;
  }
  const lines = nutrition.uncountedIngredients.map(
    (line) => `${line.name} (${UNCOUNTED_REASON_LABELS[line.reason]})`,
  );
  return `Nie wliczono: ${lines.join(', ')}.`;
}

export function describeRecipeCalories(nutrition: RecipeNutrition): KcalDisplay {
  const kcal = findRecipeKcal(nutrition);
  const uncounted = describeUncountedIngredients(nutrition);
  if (kcal === null) {
    return {
      text: UNKNOWN_KCAL_TEXT,
      isKnown: false,
      isEstimate: false,
      tooltip: uncounted,
      caption: null,
    };
  }
  const unit = nutrition.kcalPerServing === null ? 'kcal' : 'kcal/porcję';
  const notes = [nutrition.hasEstimates ? ESTIMATE_TOOLTIP : null, uncounted].filter(
    (note) => note !== null,
  );
  return {
    text: `${roundKcal(kcal)} ${unit}`,
    isKnown: true,
    isEstimate: nutrition.hasEstimates,
    tooltip: notes.length === 0 ? null : notes.join(' '),
    caption: null,
  };
}

export interface CookableSuggestion {
  suggestion: RecipeSuggestion;
  recipe: RecipeListing;
}

export function attachRecipes(
  suggestions: RecipeSuggestion[],
  recipes: RecipeListing[],
): CookableSuggestion[] {
  const recipesById = new Map(recipes.map((recipe) => [recipe.id, recipe]));
  const cookable: CookableSuggestion[] = [];
  for (const suggestion of suggestions) {
    const recipe = recipesById.get(suggestion.recipeId);
    if (recipe !== undefined) {
      cookable.push({ suggestion, recipe });
    }
  }
  return cookable;
}

export function totalTimeMinutes(recipe: RecipeSummary): number {
  return recipe.preparationTimeMinutes + recipe.cookingTimeMinutes;
}

export const RECIPE_LIST_TABS = ['suggestions', 'all', 'external'] as const;

export type RecipeListTab = (typeof RECIPE_LIST_TABS)[number];

export const RECIPE_SORTS = ['name', 'time', 'calories'] as const;

export type RecipeSort = (typeof RECIPE_SORTS)[number];

export const RECIPE_SORT_LABELS: Readonly<Record<RecipeSort, string>> = {
  name: 'Nazwa',
  time: 'Czas',
  calories: 'Kalorie',
};

export interface RecipeView {
  search: string;
  sort: RecipeSort;
  isReversed: boolean;
}

function matchesRecipeSearch(recipe: RecipeListing, search: string): boolean {
  const categoryNames = recipe.category === null ? [] : [recipe.category.name];
  const texts = [recipe.name, ...recipe.tags, ...categoryNames, ...recipe.ingredientNames];
  return matchesSearch(search, texts);
}

function toKcalKey(nutrition: RecipeNutrition): number | null {
  const kcal = findRecipeKcal(nutrition);
  return kcal === null ? null : Number(kcal);
}

function toRecipeSortKeys(recipe: RecipeListing, sort: RecipeSort): SortKey[] {
  if (sort === 'name') {
    return [recipe.name];
  }
  if (sort === 'calories') {
    return [toKcalKey(recipe.nutrition), recipe.name];
  }
  return [totalTimeMinutes(recipe), recipe.name];
}

export function arrangeRecipes(recipes: RecipeListing[], view: RecipeView): RecipeListing[] {
  const visible = recipes.filter((recipe) => matchesRecipeSearch(recipe, view.search));
  return sortByKeys(visible, (recipe) => toRecipeSortKeys(recipe, view.sort), view.isReversed);
}

function matchesSuggestion(
  entry: CookableSuggestion,
  view: RecipeView,
  isReadyOnly: boolean,
): boolean {
  const matchesReadiness = !isReadyOnly || entry.suggestion.shortfall.isReady;
  return matchesReadiness && matchesRecipeSearch(entry.recipe, view.search);
}

export function arrangeSuggestions(
  suggestions: CookableSuggestion[],
  view: RecipeView,
  isReadyOnly: boolean,
): CookableSuggestion[] {
  const visible = suggestions.filter((entry) => matchesSuggestion(entry, view, isReadyOnly));
  return sortByKeys(visible, (entry) => toRecipeSortKeys(entry.recipe, view.sort), view.isReversed);
}
