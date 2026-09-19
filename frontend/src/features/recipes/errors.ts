import { describeApiError } from '@/features/shared/apiError';

const MESSAGES: Record<string, string> = {
  recipe_not_found: 'Nie znaleziono przepisu.',
  invalid_servings: 'Nieprawidłowa liczba porcji.',
  duplicate_recipe_ingredient: 'Ten składnik występuje w przepisie więcej niż raz.',
  measurement_unit_not_found: 'Nieznana jednostka miary.',
  recipe_category_not_found: 'Nie znaleziono kategorii przepisu.',
  external_recipe_not_found: 'Nie znaleziono przepisu w zewnętrznym źródle.',
  recipe_source_unavailable: 'Zewnętrzne źródło przepisów jest niedostępne.',
  recipe_source_contract_invalid: 'Zewnętrzne źródło przepisów zwróciło nieoczekiwane dane.',
  invalid: 'Popraw dane w formularzu — backend odrzucił zapis.',
};

export function describeRecipeError(error: unknown): string {
  return describeApiError(error, MESSAGES, 'Nie udało się pobrać danych przepisów.');
}
