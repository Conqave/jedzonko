import { describeApiError } from '@/features/shared/apiError';

const MESSAGES: Record<string, string> = {
  duplicate_inventory_item: 'Ten produkt jest już w zapasach tego gospodarstwa domowego.',
  ingredient_not_found: 'Nie znaleziono wybranego składnika.',
  measurement_unit_not_found: 'Nie znaleziono wybranej jednostki miary.',
  inventory_item_not_found: 'Nie znaleziono pozycji w zapasach.',
};

export function describeInventoryError(error: unknown): string {
  return describeApiError(error, MESSAGES, 'Nie udało się wykonać operacji na zapasach.');
}
