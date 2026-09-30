import type { ErrorMessages } from '@/shared/apiError';

export const SHOPPING_ERROR_MESSAGES: ErrorMessages = {
  shopping_list_not_found: 'Nie znaleziono listy zakupów.',
  primary_shopping_list_not_found: 'To gospodarstwo nie ma głównej listy zakupów.',
  primary_shopping_list_cannot_be_deleted: 'Głównej listy zakupów nie można usunąć.',
  shopping_item_not_found: 'Nie znaleziono pozycji na liście zakupów.',
  invalid_shopping_item: 'Nieprawidłowa pozycja listy zakupów.',
  product_not_found: 'Nie znaleziono wybranego produktu.',
  ingredient_not_found: 'Nie znaleziono wybranego składnika.',
  measurement_unit_not_found: 'Nieznana jednostka miary.',
  shopping_item_already_pending: 'Ta pozycja jest już na liście.',
  shopping_item_merge_conflict: 'Tej pozycji nie da się połączyć z istniejącą.',
  shopping_item_product_ambiguous:
    'Kilka produktów ma tag tej pozycji. Kliknij „Kupiono” ponownie i wybierz produkt.',
  chosen_product_not_tagged:
    'Wybrany produkt nie ma już tagu tej pozycji. Kliknij „Kupiono” ponownie.',
  tag_product_name_taken:
    'Produkt o nazwie tagu już istnieje, ale nie ma tego tagu. Otaguj go w katalogu albo wybierz produkt dla pozycji.',
  recipe_not_found: 'Nie znaleziono przepisu.',
  external_recipe_not_found: 'Nie znaleziono przepisu w zewnętrznym źródle.',
  recipe_source_unavailable: 'Zewnętrzne źródło przepisów jest niedostępne.',
  no_shops_chosen: 'Wybierz co najmniej jeden sklep.',
  nothing_to_split: 'Na liście nie ma niekupionych pozycji do podziału.',
  promotions_not_allowed: 'Brak dostępu do promocji.',
  tagging_unavailable: 'Ollama jest chwilowo niedostępna albo zajęta. Spróbuj ponownie za chwilę.',
  promotion_source_unavailable: 'Źródło promocji jest chwilowo niedostępne.',
};
