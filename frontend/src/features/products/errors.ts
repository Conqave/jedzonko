import { describeApiError } from '@/shared/apiError';

const MESSAGES: Record<string, string> = {
  product_not_found: 'Nie znaleziono wybranego produktu.',
  duplicate_product: 'Produkt o tej nazwie już istnieje w tym gospodarstwie domowym.',
  measurement_unit_not_found: 'Nie znaleziono wybranej jednostki miary.',
  tag_proposal_not_found: 'Nie znaleziono propozycji tagu.',
  tag_proposal_not_pending: 'Ta propozycja tagu została już rozpatrzona.',
};

export function describeProductError(error: unknown): string {
  return describeApiError(error, MESSAGES);
}
