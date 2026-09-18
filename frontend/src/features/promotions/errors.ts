import axios from 'axios';
import type { ApiError } from '@/features/accounts/models';

const MESSAGES: Record<string, string> = {
  promotion_source_unavailable: 'Źródło promocji jest chwilowo niedostępne.',
  promotion_source_contract_invalid: 'Źródło promocji zwróciło nieoczekiwaną odpowiedź.',
  permission_denied: 'Brak dostępu do promocji.',
  not_authenticated: 'Sesja wygasła. Zaloguj się ponownie.',
};

export function describePromotionError(error: unknown): string {
  if (axios.isAxiosError<ApiError>(error) && error.response !== undefined) {
    const code = error.response.data?.code;
    if (code !== undefined && MESSAGES[code] !== undefined) {
      return MESSAGES[code];
    }
  }
  return 'Nie udało się pobrać promocji.';
}
