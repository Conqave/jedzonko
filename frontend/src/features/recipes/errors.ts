import { describeApiError } from '@/features/shared/apiError';

const MESSAGES: Record<string, string> = {
  recipe_not_found: 'Nie znaleziono przepisu.',
  invalid_servings: 'Nieprawidłowa liczba porcji.',
  duplicate_recipe_ingredient: 'Ten składnik występuje w przepisie więcej niż raz.',
};

export function describeRecipeError(error: unknown): string {
  return describeApiError(error, MESSAGES, 'Nie udało się pobrać danych przepisów.');
}
