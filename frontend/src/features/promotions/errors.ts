import { describeApiError } from '@/features/shared/apiError';

const MESSAGES: Record<string, string> = {
  promotion_source_unavailable: 'Źródło promocji jest chwilowo niedostępne.',
  promotion_source_contract_invalid: 'Źródło promocji zwróciło nieoczekiwaną odpowiedź.',
  permission_denied: 'Brak dostępu do promocji.',
  unknown_shop: 'Wybrany sklep nie jest obsługiwany.',
  invalid: 'Nieprawidłowe dane zapytania.',
};

export function describePromotionError(
  error: unknown,
  fallback = 'Nie udało się pobrać promocji.',
): string {
  return describeApiError(error, MESSAGES, fallback);
}
