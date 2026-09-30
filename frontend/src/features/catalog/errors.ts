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
  ingredient_classifier_unavailable: 'Model analizujący produkty jest chwilowo niedostępny.',
  ingredient_classifier_contract_invalid: 'Model zwrócił nieczytelną odpowiedź.',
  product_already_classified:
    'Produkt ma już potwierdzony składnik. Odrzuć go, aby przeanalizować ponownie.',
  invalid_product_ingredient_transition: 'Ten składnik został już odrzucony.',
  invalid_tag_calories:
    'Kalorie na 100 g to liczba od 0 do 900 z najwyżej jednym miejscem po przecinku.',
  invalid_piece_weight:
    'Waga sztuki to liczba większa od 0 i najwyżej 10000 g z najwyżej jednym miejscem po przecinku.',
  invalid_density:
    'Gęstość to liczba większa od 0 i najwyżej 3 g/ml z najwyżej trzema miejscami po przecinku.',
};
