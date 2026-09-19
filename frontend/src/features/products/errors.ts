import { describeApiError } from '@/features/shared/apiError';

const MESSAGES: Record<string, string> = {
  product_not_found: 'Nie znaleziono wybranego produktu.',
  duplicate_product: 'Produkt o tej nazwie już istnieje w tym gospodarstwie domowym.',
  measurement_unit_not_found: 'Nie znaleziono wybranej jednostki miary.',
};

export function describeProductError(error: unknown): string {
  return describeApiError(error, MESSAGES, 'Nie udało się wykonać operacji na produktach.');
}
