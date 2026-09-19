import { describeApiError } from '@/features/shared/apiError';

const MESSAGES: Record<string, string> = {
  duplicate_inventory_item: 'Ten produkt jest już w zapasach tego gospodarstwa domowego.',
  product_not_found: 'Nie znaleziono wybranego produktu.',
  measurement_unit_not_found: 'Nie znaleziono wybranej jednostki miary.',
  inventory_item_not_found: 'Nie znaleziono pozycji w zapasach.',
  inventory_category_not_found: 'Nie znaleziono wybranej kategorii.',
  duplicate_inventory_category: 'Taka kategoria już istnieje w tym gospodarstwie domowym.',
  photo_required: 'Nie wybrano pliku ze zdjęciem.',
  photo_too_large: 'Zdjęcie jest za duże (maksymalnie 5 MB).',
  unsupported_photo_type: 'Dozwolone są tylko pliki JPEG, PNG i WebP.',
  invalid_photo: 'Wybrany plik nie jest poprawnym zdjęciem.',
  inventory_photo_not_found: 'Ta pozycja nie ma zdjęcia.',
  duplicate_product: 'Produkt o tej nazwie już istnieje w tym gospodarstwie domowym.',
  empty_inventory_update: 'Nie podano żadnych zmian.',
};

export function describeInventoryError(error: unknown): string {
  return describeApiError(error, MESSAGES, 'Nie udało się wykonać operacji na zapasach.');
}
