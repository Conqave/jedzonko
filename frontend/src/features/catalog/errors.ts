import type { ErrorMessages } from '@/shared/apiError';

export const CATALOG_ERROR_MESSAGES: ErrorMessages = {
  product_not_found: 'Nie znaleziono produktu.',
  duplicate_product: 'Produkt o tej nazwie już istnieje w tym gospodarstwie domowym.',
  ingredient_not_found: 'Nie znaleziono składnika.',
  duplicate_ingredient_name: 'Ta nazwa należy już do innego składnika.',
  invalid_name: 'Nazwa jest pusta albo za długa.',
  measurement_unit_not_found: 'Nieznana jednostka miary.',
  invalid_package: 'Opakowanie musi mieć dodatnią ilość.',
  product_ingredient_not_found: 'Ten produkt nie ma takiej propozycji składnika.',
  invalid_product_ingredient_transition: 'Ten składnik został już odrzucony.',
};
