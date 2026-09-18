import { describeApiError } from '@/features/shared/apiError';

const MESSAGES: Record<string, string> = {
  user_not_found: 'Nie znaleziono użytkownika o podanej nazwie.',
  last_member_cannot_leave: 'Nie można usunąć ostatniego członka gospodarstwa domowego.',
};

export function describeHouseholdError(error: unknown): string {
  return describeApiError(
    error,
    MESSAGES,
    'Nie udało się wykonać operacji na gospodarstwie domowym.',
  );
}
