import { describeApiError } from '@/features/shared/apiError';

const MESSAGES: Record<string, string> = {
  shopping_list_not_found: 'Nie znaleziono listy zakupów.',
  shopping_item_not_found: 'Nie znaleziono pozycji na liście zakupów.',
  invalid_shopping_item: 'Nieprawidłowa pozycja listy zakupów.',
  recipe_not_found: 'Nie znaleziono przepisu.',
  invalid_servings: 'Nieprawidłowa liczba porcji.',
  product_not_found: 'Nie znaleziono wybranego produktu.',
  measurement_unit_not_found: 'Nie znaleziono wybranej jednostki miary.',
};

export function describeShoppingError(error: unknown): string {
  return describeApiError(error, MESSAGES, 'Nie udało się wykonać operacji na liście zakupów.');
}
