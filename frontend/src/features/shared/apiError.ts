import axios from 'axios';
import type { ApiError } from '@/features/accounts/models';

const COMMON_MESSAGES: Record<string, string> = {
  not_authenticated: 'Sesja wygasła. Zaloguj się ponownie.',
  not_a_household_member: 'Nie należysz do tego gospodarstwa domowego.',
  permission_denied: 'Brak uprawnień do tej operacji.',
};

export function describeApiError(
  error: unknown,
  messages: Record<string, string>,
  fallback: string,
): string {
  if (axios.isAxiosError<ApiError>(error) && error.response !== undefined) {
    const code = error.response.data?.code;
    if (code !== undefined) {
      const message = messages[code] ?? COMMON_MESSAGES[code];
      if (message !== undefined) {
        return message;
      }
    }
  }
  return fallback;
}
