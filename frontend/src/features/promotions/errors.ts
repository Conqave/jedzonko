import type { ErrorMessages } from '@/shared/apiError';

export const PROMOTION_ERROR_MESSAGES: ErrorMessages = {
  promotion_source_unavailable: 'Źródło promocji jest chwilowo niedostępne.',
  promotion_source_contract_invalid: 'Źródło promocji zwróciło nieoczekiwaną odpowiedź.',
  permission_denied: 'Brak dostępu do promocji.',
  unknown_shop: 'Wybrany sklep nie jest obsługiwany.',
  invalid_query: 'Nieprawidłowe zapytanie.',
};
